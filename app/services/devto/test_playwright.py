import asyncio
from app.services.devto.devto_playwright import register_on_devto

async def test_register():
    result = await register_on_devto(
        name="Test Name",
        username="testusername",
        email="testemail@example.com",
        password="testpassword"
    )
    print(result)

asyncio.run(test_register())