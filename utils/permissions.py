"""Module kiểm tra quyền của người dùng."""

from config import Config

def is_owner(self, user):
    return user.id == Config.OWNER_ID

def has_special_role(self, user):
    return any(role.id in Config.SPECIAL_ROLE_IDS for role in user.roles)

def can_skip(self, user):
    return user.id == self.current_requester or has_special_role(self, user) or is_owner(self, user)

def can_stop(self, user):
    return user.id == self.current_requester or has_special_role(self, user) or is_owner(self, user)