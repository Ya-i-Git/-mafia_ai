from backend.server.game.roles import Role

class Player:
    def __init__(self, user_id: str, username: str, role: Role = Role.CIVILIAN):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.number = 0 # номер игрока (порядок речей)
        self.is_alive = True
        self.nominated = False
        self.websocket = None
                  