"""
头像服务
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ...db.database.models.user import User
from ...db.storage.factory import get_storage
from ...logger.logger import logger


class AvatarService:
    """头像服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage()
    
    def upload_avatar(self, user_id: str, file_data, file_name: str, content_type: str) -> Optional[str]:
        """
        上传用户头像
        
        Args:
            user_id: 用户ID
            file_data: 文件数据
            file_name: 文件名
            content_type: 内容类型
        
        Returns:
            文件ID
        """
        try:
            # 上传文件到存储
            file_id = self.storage.upload_file(
                file_data=file_data,
                file_name=file_name,
                content_type=content_type,
                bucket_name="avatars"
            )
            
            # 更新用户头像字段
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                # 删除旧头像（如果存在）
                if user.avatar:
                    self.delete_avatar_file(user.avatar)
                
                # 更新新头像
                user.avatar = file_id
                self.db.commit()
                
                logger.info(f"用户 {user_id} 头像上传成功: {file_id}")
                return file_id
            else:
                # 用户不存在，删除已上传的文件
                self.storage.delete_file(file_id, bucket_name="avatars")
                logger.warning(f"用户 {user_id} 不存在，删除已上传的头像文件")
                return None
                
        except Exception as e:
            logger.error(f"上传头像失败: {e}")
            raise
    
    def delete_avatar(self, user_id: str) -> bool:
        """
        删除用户头像
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否删除成功
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.avatar:
                return False
            
            # 删除存储中的文件
            file_id = user.avatar
            success = self.delete_avatar_file(file_id)
            
            if success:
                # 清除用户头像字段
                user.avatar = None
                self.db.commit()
                logger.info(f"用户 {user_id} 头像删除成功")
            
            return success
            
        except Exception as e:
            logger.error(f"删除头像失败: {e}")
            return False
    
    def delete_avatar_file(self, file_id: str) -> bool:
        """
        删除头像文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否删除成功
        """
        try:
            return self.storage.delete_file(file_id, bucket_name="avatars")
        except Exception as e:
            logger.error(f"删除头像文件失败: {e}")
            return False
    
    def get_avatar_url(self, file_id: str) -> Optional[str]:
        """
        获取头像URL
        
        Args:
            file_id: 文件ID
        
        Returns:
            头像URL
        """
        try:
            return self.storage.get_file_url(file_id, bucket_name="avatars")
        except Exception as e:
            logger.error(f"获取头像URL失败: {e}")
            return None
    
    def clear_user_avatar_by_file_id(self, file_id: str) -> bool:
        """
        根据文件ID清除用户头像字段
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否清除成功
        """
        try:
            users = self.db.query(User).filter(User.avatar == file_id).all()
            for user in users:
                user.avatar = None
            
            self.db.commit()
            logger.info(f"清除 {len(users)} 个用户的头像字段")
            return True
            
        except Exception as e:
            logger.error(f"清除用户头像字段失败: {e}")
            return False 