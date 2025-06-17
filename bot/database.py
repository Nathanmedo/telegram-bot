import motor.motor_asyncio
from .vars import  DATABASE_URL, DATABASE_NAME
import datetime
from .constants import ROBOT_RATES

class Database:
    def __init__(self, uri=DATABASE_URL, database_name=DATABASE_NAME):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.pending_deposits = self.db.pending_deposits
        self.pending_withdrawals = self.db.pending_withdrawals
        self.pending_upgrades = self.db.pending_upgrades
        self.cache = {}
        print(f"Database initialized with URI: {uri} and name: {database_name}")
    
    def new_user(self, id):
        return {
            "id": id,
            "currency": "USD",
            "balance": 0,  # Mining balance
            "deposited_balance": 0,  # Deposited balance in USD
            "robot_level": 0,  # Default robot level
            "robot_counts": {  # Track number of robots at each level
                "0": 1,  # Start with 1 robot at level 0
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
                "5": 0,
                "6": 0,
                "7": 0
            },
            "mining_data": {
                "last_mined": None,
                "total_mined": 0
            },
            "referral_code": str(id),  # Use user ID as referral code
            "referred_by": None,  # ID of user who referred this user
            "referral_count": 0,  # Number of successful referrals
            "referral_earnings": 0  # Total earnings from referrals
        }
    
    async def add_user(self, id):
        """Add a new user to the database"""
        # Check if user already exists
        existing_user = await self.get_user(id)
        if existing_user:
            print(f"User {id} already exists, skipping creation")
            return existing_user
            
        user = self.new_user(id)
        print(f"Creating new user: {user}")
        await self.col.insert_one(user)
        return user
    
    async def get_user(self, id):
        user = self.cache.get(id)
        if user is not None:
            return user
        
        user = await self.col.find_one({"id": int(id)})
        self.cache[id] = user
        return user
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return True if user else False
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
    
    async def update_currency(self, user_id, currency):
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {'currency': currency}}
        )
        if user_id in self.cache:
            self.cache[user_id]['currency'] = currency

    async def add_pending_deposit(self, user_id, amount, currency, amount_usd):
        """Add a new pending deposit"""
        deposit = {
            "user_id": int(user_id),
            "amount": amount,
            "currency": currency,
            "amount_usd": amount_usd,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }
        await self.pending_deposits.insert_one(deposit)
        return deposit

    async def get_pending_deposit(self, user_id):
        """Get the latest pending deposit for a user"""
        return await self.pending_deposits.find_one(
            {"user_id": int(user_id), "status": "pending"},
            sort=[("created_at", -1)]
        )

    async def approve_deposit(self, user_id):
        """Approve a pending deposit and update user's deposited balance"""
        print(f"Starting approve_deposit for user {user_id}")
        deposit = await self.get_pending_deposit(user_id)
        print(f"Found pending deposit: {deposit}")
        
        if not deposit:
            print(f"No pending deposit found for user {user_id}")
            return None

        try:
            print("Updating deposit status...")
            # Update deposit status first
            update_result = await self.pending_deposits.update_one(
                {"_id": deposit["_id"]},
                {"$set": {"status": "approved", "approved_at": datetime.datetime.now().isoformat()}}
            )
            print(f"Deposit status update result: {update_result.modified_count}")

            print("Getting current user data...")
            # Get current user data
            user = await self.get_user(user_id)
            if not user:
                print(f"User {user_id} not found in database")
                return None
                
            current_deposited = user.get("deposited_balance", 0)
            new_deposited = current_deposited + deposit["amount_usd"]
            print(f"Updating deposited balance from {current_deposited} to {new_deposited}")
            
            # Update user deposited balance
            result = await self.col.update_one(
                {"id": int(user_id)},
                {"$set": {"deposited_balance": new_deposited}}
            )
            
            # Verify the update was successful
            if result.modified_count == 0:
                print(f"Failed to update deposited balance for user {user_id}")
                return None
            
            print("Clearing user cache...")
            # Clear cache for this user
            if user_id in self.cache:
                del self.cache[user_id]
            
            print("Deposit approval completed successfully")
            return deposit
            
        except Exception as e:
            print(f"Error in approve_deposit: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    async def update_balance(self, user_id, new_balance):
        """Update user balance and clear cache"""
        await self.col.update_one(
            {"id": int(user_id)},
            {"$set": {"balance": new_balance}}
        )
        # Clear cache for this user
        if user_id in self.cache:
            del self.cache[user_id]

    async def set_wallet_address(self, user_id, address):
        """Set or update user's BTC wallet address"""
        try:
            print(f"Setting wallet address for user {user_id}: {address}")
            # First ensure user exists
            if not await self.is_user_exist(user_id):
                print(f"User {user_id} does not exist, creating new user")
                await self.add_user(user_id)
            
            # Update wallet address
            result = await self.col.update_one(
                {"id": int(user_id)},
                {"$set": {"wallet_address": address}}
            )
            print(f"Wallet address update result: {result.modified_count} documents modified")
            
            # Clear cache for this user
            if user_id in self.cache:
                del self.cache[user_id]
                print(f"Cleared cache for user {user_id}")
            
            # Verify the update
            user = await self.get_user(user_id)
            saved_address = user.get("wallet_address") if user else None
            print(f"Verified saved wallet address: {saved_address}")
            
            return True
        except Exception as e:
            print(f"Error setting wallet address: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

    async def get_wallet_address(self, user_id):
        """Get user's BTC wallet address"""
        try:
            print(f"Getting wallet address for user {user_id}")
            user = await self.get_user(user_id)
            address = user.get("wallet_address") if user else None
            print(f"Retrieved wallet address: {address}")
            return address
        except Exception as e:
            print(f"Error getting wallet address: {str(e)}")
            return None

    async def add_pending_withdrawal(self, user_id, amount_btc, amount_tokens):
        """Add a new pending withdrawal"""
        withdrawal = {
            "user_id": int(user_id),
            "amount_btc": amount_btc,
            "amount_tokens": amount_tokens,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }
        await self.pending_withdrawals.insert_one(withdrawal)
        return withdrawal

    async def get_pending_withdrawal(self, user_id):
        """Get the latest pending withdrawal for a user"""
        return await self.pending_withdrawals.find_one(
            {"user_id": int(user_id), "status": "pending"},
            sort=[("created_at", -1)]
        )

    async def approve_withdrawal(self, user_id):
        """Approve a pending withdrawal and update user balance"""
        withdrawal = await self.get_pending_withdrawal(user_id)
        if not withdrawal:
            return None

        try:
            # Update withdrawal status
            await self.pending_withdrawals.update_one(
                {"_id": withdrawal["_id"]},
                {"$set": {"status": "approved", "approved_at": datetime.datetime.now().isoformat()}}
            )

            # Get current user data
            user = await self.get_user(user_id)
            if not user:
                return None

            # Update user balance
            current_balance = user.get("balance", 0)
            new_balance = current_balance - withdrawal["amount_tokens"]
            
            await self.update_balance(user_id, new_balance)
            
            return withdrawal
            
        except Exception as e:
            print(f"Error in approve_withdrawal: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    async def get_robot_level(self, user_id):
        """Get user's current robot level"""
        user = await self.get_user(user_id)
        return user.get("robot_level", 0) if user else 0

    async def get_robot_counts(self, user_id):
        """Get user's robot counts by level"""
        user = await self.get_user(user_id)
        return user.get("robot_counts", {"0": 1}) if user else {"0": 1}

    async def calculate_mining_rate(self, user_id):
        """Calculate total mining rate based on robot counts"""
        robot_counts = await self.get_robot_counts(user_id)
        total_rate = 0
        for level, count in robot_counts.items():
            if count > 0:
                # Get rate for this level from ROBOT_RATES
                rate = ROBOT_RATES.get(int(level), 0)
                total_rate += rate * count
        return total_rate

    async def add_pending_upgrade(self, user_id, current_level, target_level, amount_usd):
        """Add a new pending upgrade request"""
        upgrade = {
            "user_id": int(user_id),
            "current_level": current_level,
            "target_level": target_level,
            "amount_usd": amount_usd,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }
        await self.pending_upgrades.insert_one(upgrade)
        return upgrade

    async def get_pending_upgrade(self, user_id):
        """Get the latest pending upgrade for a user"""
        return await self.pending_upgrades.find_one(
            {"user_id": int(user_id), "status": "pending"},
            sort=[("created_at", -1)]
        )

    async def approve_upgrade(self, user_id):
        """Approve a pending upgrade and update user's robot level"""
        upgrade = await self.get_pending_upgrade(user_id)
        if not upgrade:
            return None

        try:
            # Update upgrade status
            await self.pending_upgrades.update_one(
                {"_id": upgrade["_id"]},
                {"$set": {"status": "approved", "approved_at": datetime.datetime.now().isoformat()}}
            )

            # Get current user data
            user = await self.get_user(user_id)
            if not user:
                return None

            # Update robot counts
            robot_counts = user.get("robot_counts", {"0": 1})
            current_level = str(upgrade["current_level"])
            target_level = str(upgrade["target_level"])

            # Decrease count of current level robot
            if current_level in robot_counts and robot_counts[current_level] > 0:
                robot_counts[current_level] -= 1

            # Increase count of target level robot
            if target_level not in robot_counts:
                robot_counts[target_level] = 0
            robot_counts[target_level] += 1

            # Update user's robot level and counts
            await self.col.update_one(
                {"id": int(user_id)},
                {
                    "$set": {
                        "robot_level": upgrade["target_level"],
                        "robot_counts": robot_counts
                    }
                }
            )

            # Clear cache for this user
            if user_id in self.cache:
                del self.cache[user_id]

            return upgrade

        except Exception as e:
            print(f"Error in approve_upgrade: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    async def get_referral_code(self, user_id):
        """Get user's referral code"""
        user = await self.get_user(user_id)
        return user.get("referral_code") if user else None

    async def get_referral_stats(self, user_id):
        """Get user's referral statistics"""
        user = await self.get_user(user_id)
        if not user:
            print(f"User {user_id} not found when getting referral stats")
            return None
            
        print(f"Getting referral stats for user {user_id}: {user}")
        return {
            "referral_code": user.get("referral_code"),
            "referral_count": user.get("referral_count", 0),
            "referral_earnings": user.get("referral_earnings", 0)
        }

    async def process_referral(self, user_id, referrer_id):
        """Process a new referral"""
        try:
            print(f"Processing referral: user {user_id} referred by {referrer_id}")
            # Get both users
            user = await self.get_user(user_id)
            referrer = await self.get_user(referrer_id)
            
            if not user or not referrer:
                print(f"User or referrer not found: user={user}, referrer={referrer}")
                return False
                
            # Check if user was already referred
            if user.get("referred_by"):
                print(f"User {user_id} was already referred by {user.get('referred_by')}")
                return False
                
            # Update user's referred_by
            await self.col.update_one(
                {"id": int(user_id)},
                {"$set": {"referred_by": int(referrer_id)}}
            )
            
            # Update referrer's stats and add reward
            new_count = referrer.get("referral_count", 0) + 1
            new_earnings = referrer.get("referral_earnings", 0) + 50  # 50 BTS reward
            new_balance = referrer.get("balance", 0) + 50  # Add 50 BTS to balance
            
            # Update referrer's data
            update_result = await self.col.update_one(
                {"id": int(referrer_id)},
                {
                    "$set": {
                        "referral_count": new_count,
                        "referral_earnings": new_earnings,
                        "balance": new_balance
                    }
                }
            )
            
            print(f"Updated referrer data: {update_result.modified_count} documents modified")
            
            # Clear cache for both users
            if user_id in self.cache:
                del self.cache[user_id]
            if referrer_id in self.cache:
                del self.cache[referrer_id]
                
            return True
            
        except Exception as e:
            print(f"Error processing referral: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

db = Database()