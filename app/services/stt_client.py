import os

from dotenv import load_dotenv
from sarvamai import SarvamAI

from app.utils.logger import get_logger


logger = get_logger(__name__)

load_dotenv()


def _build_client():
    try:
        api_key = os.getenv("STT_API_KEY")

        if not api_key:
            raise ValueError("STT_API_KEY is not configured in .env")

        client = SarvamAI(api_subscription_key=api_key)
        logger.info("Sarvam STT client initialized successfully.")
        return client
    except Exception:
        logger.exception("Failed to initialize Sarvam STT client.")
        raise


client = _build_client()