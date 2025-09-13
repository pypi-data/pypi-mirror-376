use std::{
    collections::{BinaryHeap, VecDeque},
    io::Read,
    mem,
    os::fd::{AsRawFd, FromRawFd},
    sync::{Arc, Mutex, RwLock, atomic},
    time::{Duration, Instant},
};

use anyhow::Result;
use mio::{Interest, Poll, Token, Waker, event, net::TcpListener};
use pyo3::prelude::*;

use crate::{
    handles::{BoxedHandle, CBHandle, Handle, TimerHandle},
    io::Source,
    log::{LogExc, log_exc_to_py_ctx},
    py::{copy_context, weakset},
    server::Server,
    tcp::{TCPReadHandle, TCPServer, TCPServerRef, TCPTransport, TCPWriteHandle},
    time::Timer,
    udp::{UDPReadHandle, UDPTransport, UDPWriteHandle},
};

enum IOHandle {
    Py(PyHandleData),
    Signals,
    TCPListener(TCPListenerHandleData),
    TCPStream(Interest),
    UDPSocket(Interest),
}

struct PyHandleData {
    interest: Interest,
    cbr: Option<Py<CBHandle>>,
    cbw: Option<Py<CBHandle>>,
}

struct TCPListenerHandleData {
    source: Source,
    server: TCPServerRef,
}

pub struct EventLoopRunState {
    buf: Box<[u8]>,
    events: event::Events,
    pub read_buf: Box<[u8]>,
    tick_last: u128,
}

#[pyclass(frozen, subclass, module = "rloop._rloop")]
pub struct EventLoop {
    idle: atomic::AtomicBool,
    io: Mutex<Poll>,
    waker: Arc<Waker>,
    handles_io: papaya::HashMap<Token, IOHandle>,
    handles_ready: Mutex<VecDeque<BoxedHandle>>,
    handles_sched: Mutex<BinaryHeap<Timer>>,
    epoch: Instant,
    counter_ready: atomic::AtomicUsize,
    ssock: RwLock<Option<(socket2::Socket, socket2::Socket)>>,
    closed: atomic::AtomicBool,
    exc_handler: RwLock<Py<PyAny>>,
    exception_handler: RwLock<Py<PyAny>>,
    executor: RwLock<Py<PyAny>>,
    sig_handlers: papaya::HashMap<u8, Py<CBHandle>>,
    sig_listening: atomic::AtomicBool,
    sig_loop_handled: atomic::AtomicBool,
    sig_wfd: RwLock<Py<PyAny>>,
    stopping: atomic::AtomicBool,
    shutdown_called_asyncgens: atomic::AtomicBool,
    shutdown_called_executor: atomic::AtomicBool,
    ssock_r: RwLock<Py<PyAny>>,
    ssock_w: RwLock<Py<PyAny>>,
    task_factory: RwLock<Py<PyAny>>,
    tcp_lstreams: papaya::HashMap<usize, papaya::HashSet<usize>>,
    tcp_transports: papaya::HashMap<usize, Py<TCPTransport>>,
    udp_transports: papaya::HashMap<usize, Py<UDPTransport>>,
    thread_id: atomic::AtomicI64,
    watcher_child: RwLock<Py<PyAny>>,
    #[pyo3(get)]
    _asyncgens: Py<PyAny>,
    #[pyo3(get)]
    _base_ctx: Py<PyAny>,
}

impl EventLoop {
    #[inline]
    fn step(&self, py: Python, state: &mut EventLoopRunState) -> std::result::Result<(), std::io::Error> {
        let mut sched_time: Option<u64> = None;
        let mut skip_poll = false;

        // compute poll timeout based on scheduled work
        if self.counter_ready.load(atomic::Ordering::Acquire) > 0 {
            sched_time = Some(0);
            // we want to skip polling when unnecessary:
            // if work is ready we check the time since last poll and skip for max 250μs
            let tick = Instant::now().duration_since(self.epoch).as_micros();
            if (tick - state.tick_last) < 250 {
                skip_poll = true;
            }
        } else {
            let guard_sched = self.handles_sched.lock().unwrap();
            if let Some(timer) = guard_sched.peek() {
                let tick = Instant::now().duration_since(self.epoch).as_micros();
                if timer.when > tick {
                    let dt = (timer.when - tick) as u64;
                    sched_time = Some(dt);
                }
            }
        }

        // I/O
        let poll_result = if skip_poll {
            Ok(())
        } else {
            let idle_swap = !matches!(sched_time, Some(0));
            if idle_swap {
                self.idle.store(true, atomic::Ordering::Release);
            }
            let res = py.detach(|| {
                let mut io = self.io.lock().unwrap();
                let res = io.poll(&mut state.events, sched_time.map(Duration::from_micros));
                if idle_swap {
                    self.idle.store(false, atomic::Ordering::Release);
                }
                if let Err(ref err) = res
                    && err.kind() == std::io::ErrorKind::Interrupted
                {
                    // if we got an interrupt, we retry ready events (as we might need to process signals)
                    let _ = io.poll(&mut state.events, Some(Duration::from_millis(0)));
                }
                res
            });
            state.tick_last = Instant::now().duration_since(self.epoch).as_micros();
            res
        };

        let mut cb_handles = {
            let mut guard_cb = self.handles_ready.lock().unwrap();
            mem::replace(&mut *guard_cb, VecDeque::with_capacity(128))
        };
        self.counter_ready
            .fetch_sub(cb_handles.len(), atomic::Ordering::Release);

        if !skip_poll {
            let io_handles = self.handles_io.pin();
            for event in &state.events {
                // NOTE: cancellation is not necessary as we have custom futures
                if let Some(io_handle) = io_handles.get(&event.token()) {
                    match io_handle {
                        IOHandle::Py(handle) => self.handle_io_py(py, event, handle, &mut cb_handles),
                        IOHandle::TCPListener(handle) => self.handle_io_tcpl(py, handle, &io_handles, &mut cb_handles),
                        IOHandle::TCPStream(_) => self.handle_io_tcps(event, &mut cb_handles),
                        IOHandle::UDPSocket(_) => self.handle_io_udp(event, &mut cb_handles),
                        IOHandle::Signals => self.handle_io_signals(py, &mut state.buf, &mut cb_handles),
                    }
                }
            }
        }

        // timers
        {
            let mut guard_sched = self.handles_sched.lock().unwrap();
            if let Some(timer) = guard_sched.peek() {
                let tick = Instant::now().duration_since(self.epoch).as_micros();
                if timer.when <= tick {
                    while let Some(timer) = guard_sched.peek() {
                        if timer.when > tick {
                            break;
                        }
                        cb_handles.push_back(guard_sched.pop().unwrap().handle);
                    }
                }
            }
        }

        // callbacks
        while let Some(handle) = cb_handles.pop_front() {
            if !handle.cancelled() {
                handle.run(py, self, state);
            }
        }

        poll_result
    }

    #[inline(always)]
    fn read_from_sock(&self, socket: &mut socket2::Socket, buf: &mut [u8]) -> usize {
        let mut len = 0;
        loop {
            match socket.read(&mut buf[len..]) {
                Ok(readn) if readn > 0 => len += readn,
                Err(err) if err.kind() == std::io::ErrorKind::Interrupted => {}
                _ => break,
            }
        }
        len
    }

    #[inline]
    fn handle_io_py(
        &self,
        py: Python,
        event: &event::Event,
        handle: &PyHandleData,
        handles: &mut VecDeque<BoxedHandle>,
    ) {
        if let Some(cbr) = &handle.cbr
            && event.is_readable()
        {
            handles.push_back(Box::new(cbr.clone_ref(py)));
        }
        if let Some(cbw) = &handle.cbw
            && event.is_writable()
        {
            handles.push_back(Box::new(cbw.clone_ref(py)));
        }
    }

    #[inline]
    fn handle_io_tcpl(
        &self,
        py: Python,
        handle: &TCPListenerHandleData,
        io_handles: &papaya::HashMapRef<'_, Token, IOHandle, std::hash::RandomState, papaya::LocalGuard<'_>>,
        handles: &mut VecDeque<BoxedHandle>,
    ) {
        if let Source::TCPListener(listener) = &handle.source {
            let guard_poll = self.io.lock().unwrap();
            let transports = self.tcp_transports.pin();
            let streams = self.tcp_lstreams.pin();
            let lstreams = streams.get(&handle.server.fd).unwrap().pin();
            while let Ok((stream, _)) = listener.accept() {
                let fd = stream.as_raw_fd() as usize;
                let token = Token(fd);
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let (pytransport, stream_handle) = handle.server.new_stream(py, stream);
                transports.insert(fd, pytransport);
                lstreams.insert(fd);
                _ = guard_poll.registry().register(&mut source, token, Interest::READABLE);
                io_handles.insert(Token(fd), IOHandle::TCPStream(Interest::READABLE));
                handles.push_back(stream_handle);
            }
            return;
        }
        unreachable!()
    }

    #[inline]
    fn handle_io_tcps(&self, event: &event::Event, handles_ready: &mut VecDeque<BoxedHandle>) {
        let fd = event.token().0;
        if event.is_readable() {
            handles_ready.push_back(Box::new(TCPReadHandle { fd }));
        } else if event.is_writable() {
            handles_ready.push_back(Box::new(TCPWriteHandle { fd }));
        }
    }

    #[inline]
    fn handle_io_udp(&self, event: &event::Event, handles_ready: &mut VecDeque<BoxedHandle>) {
        let fd = event.token().0;
        if event.is_readable() {
            handles_ready.push_back(Box::new(UDPReadHandle { fd }));
        } else if event.is_writable() {
            handles_ready.push_back(Box::new(UDPWriteHandle { fd }));
        }
    }

    #[inline]
    fn handle_io_signals(&self, py: Python, buf: &mut [u8], handles_ready: &mut VecDeque<BoxedHandle>) {
        let mut sock_guard = self.ssock.write().unwrap();
        if let Some((socket, _)) = sock_guard.as_mut() {
            let read = self.read_from_sock(socket, buf);
            if read > 0 && self.sig_listening.load(atomic::Ordering::Relaxed) {
                for sig in &buf[..read] {
                    self.sig_handle(py, *sig, handles_ready);
                }
            }
        }
    }

    #[inline]
    fn sig_handle(&self, py: Python, sig: u8, handles_ready: &mut VecDeque<BoxedHandle>) {
        if let Some(handle) = self.sig_handlers.pin().get(&sig) {
            self.sig_loop_handled.store(true, atomic::Ordering::Relaxed);

            if handle.cancelled() {
                self._sig_rem(sig);
            } else {
                handles_ready.push_back(Box::new(handle.clone_ref(py)));
            }
        }
    }

    #[inline(always)]
    fn wake(&self) {
        if self.idle.load(atomic::Ordering::Acquire) {
            _ = self.waker.wake();
        }
    }

    pub(crate) fn tcp_listener_add(&self, listener: TcpListener, server: TCPServerRef) {
        let fd = listener.as_raw_fd() as usize;
        let token = Token(fd);
        let mut source = Source::TCPListener(listener);
        let guard_poll = self.io.lock().unwrap();
        let _ = guard_poll.registry().register(&mut source, token, Interest::READABLE);
        self.tcp_lstreams.pin().insert(fd, papaya::HashSet::new());
        self.handles_io
            .pin()
            .insert(token, IOHandle::TCPListener(TCPListenerHandleData { source, server }));
    }

    pub(crate) fn tcp_listener_rem(&self, fd: usize) -> Result<bool> {
        let token = Token(fd);
        if let Some(handle) = self.handles_io.pin().remove(&token) {
            if let IOHandle::TCPListener(_) = handle {
                self.tcp_lstreams.pin().remove(&fd);
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let guard_poll = self.io.lock().unwrap();
                guard_poll.registry().deregister(&mut source)?;
                return Ok(true);
            }
            unreachable!()
        }
        Ok(false)
    }

    pub(crate) fn tcp_stream_add(&self, fd: usize, interest: Interest) {
        let token = Token(fd);
        self.handles_io.pin().update_or_insert_with(
            token,
            |io_handle| {
                if let IOHandle::TCPStream(interest_prev) = io_handle {
                    if *interest_prev == interest {
                        return IOHandle::TCPStream(interest);
                    }

                    let interests = *interest_prev | interest;
                    {
                        #[allow(clippy::cast_possible_wrap)]
                        let mut source = Source::FD(fd as i32);
                        let guard_poll = self.io.lock().unwrap();
                        _ = guard_poll.registry().reregister(&mut source, token, interests);
                    }
                    return IOHandle::TCPStream(interests);
                }
                unreachable!()
            },
            || {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                {
                    let guard_poll = self.io.lock().unwrap();
                    _ = guard_poll.registry().register(&mut source, token, interest);
                }
                IOHandle::TCPStream(interest)
            },
        );
    }

    pub(crate) fn tcp_stream_rem(&self, fd: usize, interest: Interest) {
        let token = Token(fd);

        match self.handles_io.pin().remove_if(&token, |_, io_handle| {
            if let IOHandle::TCPStream(interest_ex) = io_handle {
                return *interest_ex == interest;
            }
            false
        }) {
            Ok(None) => {}
            Ok(_) => {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let guard_poll = self.io.lock().unwrap();
                _ = guard_poll.registry().deregister(&mut source);
            }
            _ => {
                self.handles_io.pin().update(token, |io_handle| {
                    if let IOHandle::TCPStream(interest_ex) = io_handle {
                        let interest_new = interest_ex.remove(interest).unwrap();
                        #[allow(clippy::cast_possible_wrap)]
                        let mut source = Source::FD(fd as i32);
                        let guard_poll = self.io.lock().unwrap();
                        _ = guard_poll.registry().reregister(&mut source, token, interest_new);
                        return IOHandle::TCPStream(interest_new);
                    }
                    unreachable!()
                });
            }
        }
    }

    #[inline(always)]
    pub(crate) fn tcp_stream_close(&self, py: Python, fd: usize) {
        if let Some(transport) = self.tcp_transports.pin().remove(&fd)
            && let Some(lfd) = transport.borrow(py).lfd
        {
            self.tcp_lstreams.pin().get(&lfd).map(|v| v.pin().remove(&fd));
        }
    }

    #[inline(always)]
    pub(crate) fn get_tcp_transport(&self, fd: usize, py: Python) -> Py<TCPTransport> {
        self.tcp_transports.pin().get(&fd).unwrap().clone_ref(py)
    }

    pub(crate) fn with_tcp_listener_streams<T>(&self, fd: usize, func: T)
    where
        T: FnOnce(&papaya::HashSet<usize>),
    {
        if let Some(streams_ref) = self.tcp_lstreams.pin().get(&fd) {
            func(streams_ref);
        }
    }

    #[inline]
    pub(crate) fn udp_socket_add(&self, fd: usize, interest: Interest) {
        let token = Token(fd);
        self.handles_io.pin().update_or_insert_with(
            token,
            |io_handle| {
                if let IOHandle::UDPSocket(interest_prev) = io_handle {
                    if *interest_prev == interest {
                        return IOHandle::UDPSocket(interest);
                    }

                    let interests = *interest_prev | interest;
                    {
                        #[allow(clippy::cast_possible_wrap)]
                        let mut source = Source::FD(fd as i32);
                        let guard_poll = self.io.lock().unwrap();
                        _ = guard_poll.registry().reregister(&mut source, token, interests);
                    }
                    return IOHandle::UDPSocket(interests);
                }
                unreachable!()
            },
            || {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                {
                    let guard_poll = self.io.lock().unwrap();
                    _ = guard_poll.registry().register(&mut source, token, interest);
                }
                IOHandle::UDPSocket(interest)
            },
        );
    }

    #[inline]
    pub(crate) fn udp_socket_rem(&self, fd: usize, interest: Interest) {
        let token = Token(fd);

        match self.handles_io.pin().remove_if(&token, |_, io_handle| {
            if let IOHandle::UDPSocket(interest_ex) = io_handle {
                return *interest_ex == interest;
            }
            false
        }) {
            Ok(None) => {}
            Ok(_) => {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let guard_poll = self.io.lock().unwrap();
                _ = guard_poll.registry().deregister(&mut source);
            }
            _ => {
                self.handles_io.pin().update(token, |io_handle| {
                    if let IOHandle::UDPSocket(interest_ex) = io_handle {
                        let interest_new = interest_ex.remove(interest).unwrap();
                        #[allow(clippy::cast_possible_wrap)]
                        let mut source = Source::FD(fd as i32);
                        let guard_poll = self.io.lock().unwrap();
                        _ = guard_poll.registry().reregister(&mut source, token, interest_new);
                        return IOHandle::UDPSocket(interest_new);
                    }
                    unreachable!()
                });
            }
        }
    }

    #[inline]
    pub(crate) fn udp_socket_close(&self, fd: usize) {
        self.udp_transports.pin().remove(&fd);
    }

    #[inline(always)]
    pub(crate) fn get_udp_transport(&self, fd: usize, py: Python) -> Py<UDPTransport> {
        self.udp_transports.pin().get(&fd).unwrap().clone_ref(py)
    }

    pub(crate) fn log_exception(&self, py: Python, ctx: LogExc) -> PyResult<Py<PyAny>> {
        let handler = self.exc_handler.read().unwrap();
        handler.call1(
            py,
            (
                log_exc_to_py_ctx(py, ctx),
                self.exception_handler.read().unwrap().clone_ref(py),
            ),
        )
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule0(&self, callback: Py<PyAny>, context: Option<Py<PyAny>>) -> Result<()> {
        let handle = Python::attach(|py| {
            Py::new(
                py,
                CBHandle::new0(callback, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
            )
        })?;
        {
            let mut guard = self
                .handles_ready
                .lock()
                .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
            guard.push_back(Box::new(handle));
        }
        self.counter_ready.fetch_add(1, atomic::Ordering::Release);
        self.wake();

        Ok(())
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule1(&self, callback: Py<PyAny>, arg: Py<PyAny>, context: Option<Py<PyAny>>) -> Result<()> {
        let handle = Python::attach(|py| {
            Py::new(
                py,
                CBHandle::new1(callback, arg, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
            )
        })?;
        {
            let mut guard = self
                .handles_ready
                .lock()
                .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
            guard.push_back(Box::new(handle));
        }
        self.counter_ready.fetch_add(1, atomic::Ordering::Release);
        self.wake();

        Ok(())
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule(&self, callback: Py<PyAny>, args: Py<PyAny>, context: Option<Py<PyAny>>) -> Result<()> {
        let handle = Python::attach(|py| {
            Py::new(
                py,
                CBHandle::new1(callback, args, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
            )
        })?;
        {
            let mut guard = self
                .handles_ready
                .lock()
                .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
            guard.push_back(Box::new(handle));
        }
        self.counter_ready.fetch_add(1, atomic::Ordering::Release);
        self.wake();

        Ok(())
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule_later0(&self, delay: Duration, callback: Py<PyAny>, context: Option<Py<PyAny>>) -> Result<()> {
        let when = (Instant::now().duration_since(self.epoch) + delay).as_micros();
        let handle = Python::attach(|py| {
            Py::new(
                py,
                CBHandle::new0(callback, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
            )
        })?;
        let timer = Timer {
            handle: Box::new(handle),
            when,
        };
        {
            let mut guard = self
                .handles_sched
                .lock()
                .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
            guard.push(timer);
        }
        self.wake();

        Ok(())
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule_later1(
        &self,
        delay: Duration,
        callback: Py<PyAny>,
        arg: Py<PyAny>,
        context: Option<Py<PyAny>>,
    ) -> Result<()> {
        let when = (Instant::now().duration_since(self.epoch) + delay).as_micros();
        let handle = Python::attach(|py| {
            Py::new(
                py,
                CBHandle::new1(callback, arg, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
            )
        })?;
        let timer = Timer {
            handle: Box::new(handle),
            when,
        };
        {
            let mut guard = self
                .handles_sched
                .lock()
                .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
            guard.push(timer);
        }
        self.wake();

        Ok(())
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule_later(
        &self,
        delay: Duration,
        callback: Py<PyAny>,
        args: Py<PyAny>,
        context: Option<Py<PyAny>>,
    ) -> Result<()> {
        let when = (Instant::now().duration_since(self.epoch) + delay).as_micros();
        let handle = Python::attach(|py| {
            Py::new(
                py,
                CBHandle::new(callback, args, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
            )
        })?;
        let timer = Timer {
            handle: Box::new(handle),
            when,
        };
        {
            let mut guard = self
                .handles_sched
                .lock()
                .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
            guard.push(timer);
        }
        self.wake();

        Ok(())
    }

    #[allow(clippy::missing_errors_doc)]
    pub fn schedule_handle(&self, handle: impl Handle + Send + 'static, delay: Option<Duration>) -> Result<()> {
        match delay {
            Some(delay) => {
                let when = (Instant::now().duration_since(self.epoch) + delay).as_micros();
                let timer = Timer {
                    handle: Box::new(handle),
                    when,
                };
                {
                    let mut guard = self
                        .handles_sched
                        .lock()
                        .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
                    guard.push(timer);
                }
            }
            None => {
                {
                    let mut guard = self
                        .handles_ready
                        .lock()
                        .map_err(|_| anyhow::anyhow!("lock acquisition failed"))?;
                    guard.push_back(Box::new(handle));
                }
                self.counter_ready.fetch_add(1, atomic::Ordering::Release);
            }
        }
        self.wake();

        Ok(())
    }
}

#[pymethods]
impl EventLoop {
    #[new]
    fn new(py: Python) -> PyResult<Self> {
        let poll = Poll::new()?;
        let waker = Waker::new(poll.registry(), Token(0))?;

        Ok(Self {
            idle: atomic::AtomicBool::new(false),
            io: Mutex::new(poll),
            waker: Arc::new(waker),
            handles_io: papaya::HashMap::with_capacity(128),
            handles_ready: Mutex::new(VecDeque::with_capacity(128)),
            handles_sched: Mutex::new(BinaryHeap::with_capacity(32)),
            epoch: Instant::now(),
            counter_ready: atomic::AtomicUsize::new(0),
            ssock: RwLock::new(None),
            closed: atomic::AtomicBool::new(false),
            exc_handler: RwLock::new(py.None()),
            exception_handler: RwLock::new(py.None()),
            executor: RwLock::new(py.None()),
            sig_handlers: papaya::HashMap::with_capacity(32),
            sig_listening: atomic::AtomicBool::new(false),
            sig_loop_handled: atomic::AtomicBool::new(false),
            sig_wfd: RwLock::new(py.None()),
            stopping: atomic::AtomicBool::new(false),
            shutdown_called_asyncgens: atomic::AtomicBool::new(false),
            shutdown_called_executor: atomic::AtomicBool::new(false),
            ssock_r: RwLock::new(py.None()),
            ssock_w: RwLock::new(py.None()),
            task_factory: RwLock::new(py.None()),
            tcp_lstreams: papaya::HashMap::with_capacity(32),
            tcp_transports: papaya::HashMap::with_capacity(1024),
            udp_transports: papaya::HashMap::with_capacity(1024),
            thread_id: atomic::AtomicI64::new(0),
            watcher_child: RwLock::new(py.None()),
            _asyncgens: weakset(py)?.unbind(),
            _base_ctx: copy_context(py),
        })
    }

    #[getter(_clock)]
    fn _get_clock(&self) -> u128 {
        Instant::now().duration_since(self.epoch).as_micros()
    }

    #[getter(_thread_id)]
    fn _get_thread_id(&self) -> i64 {
        self.thread_id.load(atomic::Ordering::Relaxed)
    }

    #[setter(_thread_id)]
    fn _set_thread_id(&self, val: i64) {
        self.thread_id.store(val, atomic::Ordering::Relaxed);
    }

    #[getter(_closed)]
    fn _get_closed(&self) -> bool {
        self.closed.load(atomic::Ordering::Acquire)
    }

    #[setter(_closed)]
    fn _set_closed(&self, val: bool) {
        self.closed.store(val, atomic::Ordering::Release);
    }

    #[getter(_stopping)]
    fn _get_stopping(&self) -> bool {
        self.stopping.load(atomic::Ordering::Acquire)
    }

    #[setter(_stopping)]
    fn _set_stopping(&self, val: bool) {
        self.stopping.store(val, atomic::Ordering::Release);
    }

    #[getter(_asyncgens_shutdown_called)]
    fn _get_asyncgens_shutdown_called(&self) -> bool {
        self.shutdown_called_asyncgens.load(atomic::Ordering::Relaxed)
    }

    #[setter(_asyncgens_shutdown_called)]
    fn _set_asyncgens_shutdown_called(&self, val: bool) {
        self.shutdown_called_asyncgens.store(val, atomic::Ordering::Relaxed);
    }

    #[getter(_default_executor)]
    fn _get_default_executor(&self, py: Python) -> Py<PyAny> {
        self.executor.read().unwrap().clone_ref(py)
    }

    #[setter(_default_executor)]
    fn _set_default_executor(&self, val: Py<PyAny>) {
        let mut guard = self.executor.write().unwrap();
        *guard = val;
    }

    #[getter(_exc_handler)]
    fn _get_exc_handler(&self, py: Python) -> Py<PyAny> {
        self.exc_handler.read().unwrap().clone_ref(py)
    }

    #[setter(_exc_handler)]
    fn _set_exc_handler(&self, val: Py<PyAny>) {
        let mut guard = self.exc_handler.write().unwrap();
        *guard = val;
    }

    #[getter(_exception_handler)]
    fn _get_exception_handler(&self, py: Python) -> Py<PyAny> {
        self.exception_handler.read().unwrap().clone_ref(py)
    }

    #[setter(_exception_handler)]
    fn _set_exception_handler(&self, val: Py<PyAny>) {
        let mut guard = self.exception_handler.write().unwrap();
        *guard = val;
    }

    #[getter(_executor_shutdown_called)]
    fn _get_executor_shutdown_called(&self) -> bool {
        self.shutdown_called_executor.load(atomic::Ordering::Relaxed)
    }

    #[setter(_executor_shutdown_called)]
    fn _set_executor_shutdown_called(&self, val: bool) {
        self.shutdown_called_executor.store(val, atomic::Ordering::Relaxed);
    }

    #[getter(_sig_listening)]
    fn _get_sig_listening(&self) -> bool {
        self.sig_listening.load(atomic::Ordering::Relaxed)
    }

    #[setter(_sig_listening)]
    fn _set_sig_listening(&self, val: bool) {
        self.sig_listening.store(val, atomic::Ordering::Relaxed);
    }

    #[getter(_sig_wfd)]
    fn _get_sig_wfd(&self, py: Python) -> Py<PyAny> {
        self.sig_wfd.read().unwrap().clone_ref(py)
    }

    #[setter(_sig_wfd)]
    fn _set_sig_wfd(&self, val: Py<PyAny>) {
        let mut guard = self.sig_wfd.write().unwrap();
        *guard = val;
    }

    #[getter(_ssock_r)]
    fn _get_ssock_r(&self, py: Python) -> Py<PyAny> {
        self.ssock_r.read().unwrap().clone_ref(py)
    }

    #[setter(_ssock_r)]
    fn _set_ssock_r(&self, val: Py<PyAny>) {
        let mut guard = self.ssock_r.write().unwrap();
        *guard = val;
    }

    #[getter(_ssock_w)]
    fn _get_ssock_w(&self, py: Python) -> Py<PyAny> {
        self.ssock_w.read().unwrap().clone_ref(py)
    }

    #[setter(_ssock_w)]
    fn _set_ssock_w(&self, val: Py<PyAny>) {
        let mut guard = self.ssock_w.write().unwrap();
        *guard = val;
    }

    #[getter(_task_factory)]
    fn _get_task_factory(&self, py: Python) -> Py<PyAny> {
        self.task_factory.read().unwrap().clone_ref(py)
    }

    #[setter(_task_factory)]
    fn _set_task_factory(&self, factory: Py<PyAny>) {
        let mut guard = self.task_factory.write().unwrap();
        *guard = factory;
    }

    #[getter(_watcher_child)]
    fn _get_watcher_child(&self, py: Python) -> Py<PyAny> {
        self.watcher_child.read().unwrap().clone_ref(py)
    }

    #[setter(_watcher_child)]
    fn _set_watcher_child(&self, factory: Py<PyAny>) {
        let mut guard = self.watcher_child.write().unwrap();
        *guard = factory;
    }

    fn _ssock_set(&self, fd_r: usize, fd_w: usize) -> PyResult<()> {
        {
            let mut guard = self.ssock.write().unwrap();
            *guard = Some(unsafe {
                (
                    #[allow(clippy::cast_possible_wrap)]
                    socket2::Socket::from_raw_fd(fd_r as i32),
                    #[allow(clippy::cast_possible_wrap)]
                    socket2::Socket::from_raw_fd(fd_w as i32),
                )
            });
        }

        let token = Token(fd_r);
        let mut source = Source::FD(fd_r.try_into()?);
        let interest = Interest::READABLE;

        {
            let guard_poll = self.io.lock().unwrap();
            guard_poll.registry().register(&mut source, token, interest)?;
        }
        self.handles_io.pin().insert(token, IOHandle::Signals);

        Ok(())
    }

    fn _ssock_del(&self, fd_r: usize) -> PyResult<()> {
        let token = Token(fd_r);
        if let Some(IOHandle::Signals) = self.handles_io.pin().remove(&token) {
            #[allow(clippy::cast_possible_wrap)]
            let mut source = Source::FD(fd_r as i32);
            let guard_poll = self.io.lock().unwrap();
            guard_poll.registry().deregister(&mut source)?;
        }
        self.ssock.write().unwrap().take();

        Ok(())
    }

    #[pyo3(signature = (callback, *args, context=None))]
    fn call_soon(&self, py: Python, callback: Py<PyAny>, args: Py<PyAny>, context: Option<Py<PyAny>>) -> Py<CBHandle> {
        let handle = Py::new(
            py,
            CBHandle::new(callback, args, context.unwrap_or_else(|| copy_context(py))),
        )
        .unwrap();
        let bhandle = Box::new(handle.clone_ref(py));
        {
            let mut guard = self.handles_ready.lock().unwrap();
            guard.push_back(bhandle);
        }
        self.counter_ready.fetch_add(1, atomic::Ordering::Release);

        handle
    }

    #[pyo3(signature = (callback, *args, context=None))]
    fn call_soon_threadsafe(
        &self,
        py: Python,
        callback: Py<PyAny>,
        args: Py<PyAny>,
        context: Option<Py<PyAny>>,
    ) -> Py<CBHandle> {
        let handle = Py::new(
            py,
            CBHandle::new(callback, args, context.unwrap_or_else(|| self._base_ctx.clone_ref(py))),
        )
        .unwrap();
        let bhandle = Box::new(handle.clone_ref(py));

        {
            let mut guard = self.handles_ready.lock().unwrap();
            guard.push_back(bhandle);
        }
        self.counter_ready.fetch_add(1, atomic::Ordering::Release);
        self.wake();

        handle
    }

    fn _call_later(
        &self,
        py: Python,
        delay: u64,
        callback: Py<PyAny>,
        args: Py<PyAny>,
        context: Py<PyAny>,
    ) -> TimerHandle {
        let when = Instant::now().duration_since(self.epoch).as_micros() + u128::from(delay);
        let handle = Py::new(py, CBHandle::new(callback, args, context)).unwrap();
        let timer = Timer {
            handle: Box::new(handle.clone_ref(py)),
            when,
        };
        {
            let mut guard = self.handles_sched.lock().unwrap();
            guard.push(timer);
        }

        TimerHandle::new(handle, when)
    }

    #[pyo3(signature = (fd, callback, *args, context=None))]
    fn add_reader(
        &self,
        py: Python,
        fd: usize,
        callback: Py<PyAny>,
        args: Py<PyAny>,
        context: Option<Py<PyAny>>,
    ) -> Py<CBHandle> {
        let token = Token(fd);
        let handle = Py::new(
            py,
            CBHandle::new(callback, args, context.unwrap_or_else(|| copy_context(py))),
        )
        .unwrap();

        self.handles_io.pin().update_or_insert_with(
            token,
            |io_handle| {
                if let IOHandle::Py(data) = io_handle {
                    let interest = data.interest | Interest::READABLE;
                    #[allow(clippy::cast_possible_wrap)]
                    let mut source = Source::FD(fd as i32);
                    let guard_poll = self.io.lock().unwrap();
                    _ = guard_poll.registry().reregister(&mut source, token, data.interest);
                    return IOHandle::Py(PyHandleData {
                        interest,
                        cbr: Some(handle.clone_ref(py)),
                        cbw: Some(data.cbw.as_ref().unwrap().clone_ref(py)),
                    });
                }
                unreachable!()
            },
            || {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let interest = Interest::READABLE;
                {
                    let guard_poll = self.io.lock().unwrap();
                    _ = guard_poll.registry().register(&mut source, token, interest);
                }
                IOHandle::Py(PyHandleData {
                    interest,
                    cbr: Some(handle.clone_ref(py)),
                    cbw: None,
                })
            },
        );

        handle
    }

    fn remove_reader(&self, py: Python, fd: usize) -> bool {
        let token = Token(fd);

        match self.handles_io.pin().remove_if(&token, |_, io_handle| {
            if let IOHandle::Py(data) = io_handle {
                return data.interest == Interest::READABLE;
            }
            false
        }) {
            Ok(None) => false,
            Ok(_) => {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let guard_poll = self.io.lock().unwrap();
                _ = guard_poll.registry().deregister(&mut source);
                true
            }
            _ => {
                self.handles_io.pin().update(token, |io_handle| {
                    if let IOHandle::Py(data) = io_handle {
                        let interest = Interest::WRITABLE;
                        #[allow(clippy::cast_possible_wrap)]
                        let mut source = Source::FD(fd as i32);
                        let guard_poll = self.io.lock().unwrap();
                        _ = guard_poll.registry().reregister(&mut source, token, interest);
                        return IOHandle::Py(PyHandleData {
                            interest,
                            cbr: None,
                            cbw: Some(data.cbw.as_ref().unwrap().clone_ref(py)),
                        });
                    }
                    unreachable!()
                });
                true
            }
        }
    }

    #[pyo3(signature = (fd, callback, *args, context=None))]
    fn add_writer(
        &self,
        py: Python,
        fd: usize,
        callback: Py<PyAny>,
        args: Py<PyAny>,
        context: Option<Py<PyAny>>,
    ) -> Py<CBHandle> {
        let token = Token(fd);
        let handle = Py::new(
            py,
            CBHandle::new(callback, args, context.unwrap_or_else(|| copy_context(py))),
        )
        .unwrap();

        self.handles_io.pin().update_or_insert_with(
            token,
            |io_handle| {
                if let IOHandle::Py(data) = io_handle {
                    let interest = data.interest | Interest::WRITABLE;
                    #[allow(clippy::cast_possible_wrap)]
                    let mut source = Source::FD(fd as i32);
                    let guard_poll = self.io.lock().unwrap();
                    _ = guard_poll.registry().reregister(&mut source, token, data.interest);
                    return IOHandle::Py(PyHandleData {
                        interest,
                        cbr: Some(data.cbr.as_ref().unwrap().clone_ref(py)),
                        cbw: Some(handle.clone_ref(py)),
                    });
                }
                unreachable!()
            },
            || {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let interest = Interest::WRITABLE;
                {
                    let guard_poll = self.io.lock().unwrap();
                    _ = guard_poll.registry().register(&mut source, token, interest);
                }
                IOHandle::Py(PyHandleData {
                    interest,
                    cbr: None,
                    cbw: Some(handle.clone_ref(py)),
                })
            },
        );

        handle
    }

    fn remove_writer(&self, py: Python, fd: usize) -> bool {
        let token = Token(fd);

        match self.handles_io.pin().remove_if(&token, |_, io_handle| {
            if let IOHandle::Py(data) = io_handle {
                return data.interest == Interest::WRITABLE;
            }
            false
        }) {
            Ok(None) => false,
            Ok(_) => {
                #[allow(clippy::cast_possible_wrap)]
                let mut source = Source::FD(fd as i32);
                let guard_poll = self.io.lock().unwrap();
                _ = guard_poll.registry().deregister(&mut source);
                true
            }
            _ => {
                self.handles_io.pin().update(token, |io_handle| {
                    if let IOHandle::Py(data) = io_handle {
                        let interest = Interest::READABLE;
                        #[allow(clippy::cast_possible_wrap)]
                        let mut source = Source::FD(fd as i32);
                        let guard_poll = self.io.lock().unwrap();
                        _ = guard_poll.registry().reregister(&mut source, token, interest);
                        return IOHandle::Py(PyHandleData {
                            interest,
                            cbr: Some(data.cbr.as_ref().unwrap().clone_ref(py)),
                            cbw: None,
                        });
                    }
                    unreachable!()
                });
                true
            }
        }
    }

    fn _tcp_conn(
        pyself: Py<Self>,
        py: Python,
        sock: (i32, i32),
        protocol_factory: Py<PyAny>,
    ) -> PyResult<(Py<TCPTransport>, Py<PyAny>)> {
        let rself = pyself.get();
        let transport = TCPTransport::from_py(py, &pyself, sock, protocol_factory);
        let fd = transport.fd;
        let pytransport = Py::new(py, transport)?;
        let proto = TCPTransport::attach(&pytransport, py)?;
        rself.tcp_transports.pin().insert(fd, pytransport.clone_ref(py));
        rself.tcp_stream_add(fd, Interest::READABLE);
        Ok((pytransport, proto))
    }

    fn _tcp_server(
        pyself: Py<Self>,
        py: Python,
        socks: Py<PyAny>,
        rsocks: Vec<(i32, i32)>,
        protocol_factory: Py<PyAny>,
        backlog: i32,
    ) -> PyResult<Py<Server>> {
        let mut servers = Vec::new();
        for (fd, family) in rsocks {
            servers.push(TCPServer::from_fd(fd, family, backlog, protocol_factory.clone_ref(py)));
        }
        let server = Server::tcp(pyself.clone_ref(py), socks, servers);
        Py::new(py, server)
    }

    fn _tcp_stream_bound(&self, fd: usize) -> bool {
        self.tcp_transports.pin().contains_key(&fd)
    }

    fn _udp_conn(
        pyself: Py<Self>,
        py: Python,
        sock: (i32, i32),
        protocol_factory: Py<PyAny>,
        remote_addr: Option<(String, u16)>,
    ) -> PyResult<(Py<UDPTransport>, Py<PyAny>)> {
        let rself = pyself.get();
        let transport = UDPTransport::from_py(py, &pyself, sock, protocol_factory, remote_addr);
        let fd = transport.fd;
        let pytransport = Py::new(py, transport)?;
        let proto = UDPTransport::attach(&pytransport, py)?;
        rself.udp_transports.pin().insert(fd, pytransport.clone_ref(py));
        rself.udp_socket_add(fd, Interest::READABLE);
        Ok((pytransport, proto))
    }

    fn _sig_add(&self, py: Python, sig: u8, callback: Py<PyAny>, args: Py<PyAny>, context: Py<PyAny>) {
        let handle = Py::new(py, CBHandle::new(callback, args, context)).unwrap();
        self.sig_handlers.pin().insert(sig, handle);
    }

    fn _sig_rem(&self, sig: u8) -> bool {
        self.sig_handlers.pin().remove(&sig).is_some()
    }

    fn _sig_clear(&self) {
        self.sig_handlers.pin().clear();
    }

    fn _run(&self, py: Python) -> PyResult<()> {
        let mut state = EventLoopRunState {
            buf: vec![0; 4096].into_boxed_slice(),
            events: event::Events::with_capacity(128),
            read_buf: vec![0; 262_144].into_boxed_slice(),
            tick_last: 0,
        };

        loop {
            if self.stopping.load(atomic::Ordering::Acquire) {
                break;
            }
            if let Err(err) = self.step(py, &mut state) {
                if err.kind() == std::io::ErrorKind::Interrupted {
                    if self.sig_loop_handled.swap(false, atomic::Ordering::Relaxed) {
                        continue;
                    }
                    break;
                }
                return Err(err.into());
            }
        }

        Ok(())
    }
}

pub(crate) fn init_pymodule(module: &Bound<PyModule>) -> PyResult<()> {
    module.add_class::<EventLoop>()?;

    Ok(())
}
