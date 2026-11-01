import os

import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    uvicorn.run("autopilot.app:create_app", factory=True,
                host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8877")),
                workers=1, access_log=False)
