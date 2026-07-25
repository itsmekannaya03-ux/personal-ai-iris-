import traceback
import asyncio
from api.core.database import async_session
from api.models.user import User
from api.core.security import hash_password
from api.models.subscription import Subscription, PlanEnum

async def test():
    try:
        async with async_session() as db:
            user = User(
                email="test_signup@test.com",
                password_hash=hash_password("123"),
                name="test",
            )
            db.add(user)
            await db.flush()

            sub = Subscription(user_id=user.id, plan=PlanEnum.free)
            db.add(sub)
            await db.commit()
            print("Signup successful")
    except Exception as e:
        with open("error_log.txt", "w") as f:
            traceback.print_exc(file=f)

asyncio.run(test())
