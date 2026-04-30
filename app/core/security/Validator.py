import re
from typing import Tuple

from app.core.logging.Logger import logger
from app.core.security.SensitiveWordFilter import get_sensitive_word_filter


class Validator:
    """验证工具类"""
    
    INVISIBLE_CHARS = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u00a0', '\u3000']
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        验证用户名
        规则：只能包含英文、数字、下划线，长度4-20位
        """
        if not username or not isinstance(username, str):
            return False, "用户名不能为空"
        
        username = username.strip()
        
        if len(username) < 4 or len(username) > 20:
            return False, "用户名长度必须在4-20位之间"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "用户名只能包含英文、数字和下划线"
        
        return True, "用户名合法"
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        验证密码
        规则：只能包含英文、数字、英文标点符号，长度6-20位
        """
        if not password or not isinstance(password, str):
            return False, "密码不能为空"
        
        if len(password) < 6 or len(password) > 20:
            return False, "密码长度必须在6-20位之间"
        
        if not re.match(r'^[a-zA-Z0-9!"#$%&\'()*+,-./:;<=>?@[\\\]^_`{|}~]+$', password):
            return False, "密码只能包含英文、数字和英文标点符号"
        
        return True, "密码合法"
    
    @staticmethod
    def validate_nickname(nickname: str) -> Tuple[bool, str]:
        """
        验证昵称
        规则：
        1. 长度4-10位
        2. 不能包含空格和不可见字符
        3. 不能全是数字
        4. 不能包含敏感词
        """
        if not nickname or not isinstance(nickname, str):
            return False, "昵称不能为空"
        
        nickname = nickname.strip()
        
        if len(nickname) < 4 or len(nickname) > 10:
            return False, "昵称长度必须在4-10位之间"
        
        if ' ' in nickname:
            return False, "昵称不能包含空格"
        
        for char in Validator.INVISIBLE_CHARS:
            if char in nickname:
                return False, "昵称包含非法字符"
        
        if nickname.isdigit():
            return False, "昵称不能全是数字"
        
        try:
            sensitive_filter = get_sensitive_word_filter()
            if sensitive_filter.check(nickname):
                return False, "昵称包含敏感词汇"
        except Exception:
            # 检测器异常时放行，保持服务可用性
            logger.exception("[VALIDATOR] nickname sensitive check failed, fallback pass")
        
        return True, "昵称合法"
    
    @staticmethod
    def validate_username_password_different(username: str, password: str) -> Tuple[bool, str]:
        """验证用户名和密码不能相同"""
        if username == password:
            return False, "用户名和密码不能相同"
        return True, "验证通过"
