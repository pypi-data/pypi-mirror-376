from fasthtml.common import *
from monsterui.all import *
from dataclasses import dataclass
from .middleware import AuthBeforeware
from .database import AuthDatabase
from .repository import UserRepository
from .routes import AuthRoutes
from .models import User

class AuthManager:
    """ A class to manage user authentication and route access for fasthtml apps.  Intended to be
    modular to enable easy re-use

    Methods:
        initialize: Initialize the auth system and database
        create_beforeware: Create authentication middleware  
        register_routes: Register authentication routes
        require_role: Decorator for role-based access control
        require_admin: Decorator for admin-only access
        get_user: Get user by username 

    """
    def __init__(self, db_path="data/app.db", config=None):
        self.config = config or {}
        self.auth_db = AuthDatabase(db_path)
        self.middleware = AuthBeforeware(self, self.config)
        self.db=None
        self.routes = {}  # Store route references
        self.user_repo = None
        self.route_handler = AuthRoutes(self)

    def initialize(self):
        """Initialise the auth system"""
        # Create tables
        self.db = self.auth_db.initialize_auth_tables()

        # Create repo to manage users
        self.user_repo = UserRepository(self.db)

        # Create default admin
        self._create_default_admin()

        admin = self.get_user('admin')
        (f"Admin User class: {type(admin)}")
        print(f"Are they the same class? {type(admin) is User}")    
        
        return self.db
    
    def create_beforeware(self, additional_public_paths=None):
        return self.middleware.create_beforeware(additional_public_paths)

    def require_role(self, *roles):
        """Get role requirement decorator"""
        return self.middleware.require_role(*roles)

    def require_admin(self):
        """Get admin requirement decorator"""
        return self.middleware.require_admin()

    def get_user(self, username: str):
        return self.user_repo.get_by_username(username)
    
    def register_routes(self, app, prefix='/auth', include_admin=False):
        """
        Register authentication routes with optional admin interface
        
        Args:
            app: FastHTML application instance
            prefix: URL prefix for auth routes (default: /auth)
            include_admin: Enable admin user management interface (default: False)
                - Adds /auth/admin dashboard
                - Adds /auth/admin/users for user management
                - Adds CRUD operations for users
        
        Returns:
            Dictionary of registered routes
        
        Example:
            # Basic auth without admin interface
            auth.register_routes(app)
            
            # Include admin interface for user management
            auth.register_routes(app, include_admin=True)
        """
        return self.route_handler.register_all(app, prefix, include_admin=include_admin)
    
    # Create default admin
    def _create_default_admin(self):
        """Create default admin if needed"""
        if not self.user_repo.get_by_username('admin'):
            self.user_repo.create(
                username='admin',
                email='admin@system.local',
                password='admin123',  # Will be hashed by repository
                role='admin'
            )
    

