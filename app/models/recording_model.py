from sqlalchemy import Column, Integer, LargeBinary, String, Text, TIMESTAMP
from sqlalchemy.sql import func

from app.database import Base


class SpeechRecording(Base):
    __tablename__ = "speech_recordings"

    recording_id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    audio_data = Column(LargeBinary, nullable=False)
    transcript = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
