import socket
import threading
import json
import time

BROADCAST_PORT = 50000
SERVER_PORT = 50001
BROADCAST_MESSAGE = 'ShooterGameServer'


class LANServer:
    """Simple LAN server for 1v1 games.

    The server periodically broadcasts its presence on the local network and
    sends the local player's state to the connected client.  It also receives
    state updates from the remote player and applies them.
    """

    def __init__(self):
        self.local_player = None
        self.remote_player = None
        self.client_conn = None
        self.running = False

    def start(self, local_player, remote_player):
        self.local_player = local_player
        self.remote_player = remote_player
        self.running = True
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.running:
            try:
                sock.sendto(BROADCAST_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))
                time.sleep(1)
            except Exception:
                break
        sock.close()

    def _accept_loop(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('', SERVER_PORT))
        srv.listen(1)
        conn, _ = srv.accept()
        self.client_conn = conn
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _recv_loop(self):
        while self.running and self.client_conn:
            try:
                data = self.client_conn.recv(1024)
                if not data:
                    break
                state = json.loads(data.decode())
                if self.remote_player:
                    self.remote_player.apply_network_state(state)
            except Exception:
                break
        if self.client_conn:
            self.client_conn.close()
            self.client_conn = None

    def update(self):
        if not self.client_conn or not self.local_player:
            return
        state = {
            'pos': list(self.local_player.position),
            'rot_y': self.local_player.rotation_y,
        }
        try:
            self.client_conn.send(json.dumps(state).encode())
        except Exception:
            pass


class LANClient:
    """Client that connects to a LAN server and synchronises player state."""

    def __init__(self):
        self.local_player = None
        self.remote_player = None
        self.sock = None
        self.running = False

    def discover(self, timeout=3):
        """Listen for broadcast messages and return a list of server IPs."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', BROADCAST_PORT))
        sock.settimeout(timeout)
        servers = set()
        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                if data.decode() == BROADCAST_MESSAGE:
                    servers.add(addr[0])
            except socket.timeout:
                continue
            except Exception:
                break
        sock.close()
        return list(servers)

    def connect(self, server_ip):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_ip, SERVER_PORT))
        self.running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def start(self, local_player, remote_player):
        self.local_player = local_player
        self.remote_player = remote_player

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                state = json.loads(data.decode())
                if self.remote_player:
                    self.remote_player.apply_network_state(state)
            except Exception:
                break
        if self.sock:
            self.sock.close()
            self.sock = None

    def update(self):
        if not self.sock or not self.local_player:
            return
        state = {
            'pos': list(self.local_player.position),
            'rot_y': self.local_player.rotation_y,
        }
        try:
            self.sock.send(json.dumps(state).encode())
        except Exception:
            pass
