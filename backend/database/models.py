from typing import Optional
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import String, Boolean, Enum, Integer, Float, ForeignKey
from pipeline.categories import ImageType, Subject, ArtTechnique

Base = declarative_base()


class Artwork(Base):
    __tablename__ = "artworks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    file_type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    file_extension: Mapped[str] = mapped_column(String)
    image_type: Mapped[Optional[ImageType]] = mapped_column(
        Enum(ImageType), nullable=True
    )
    subject: Mapped[Optional[Subject]] = mapped_column(Enum(Subject), nullable=True)
    art_technique: Mapped[Optional[ArtTechnique]] = mapped_column(
        Enum(ArtTechnique), nullable=True
    )
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    colors: Mapped[list["ArtworkColor"]] = relationship(
        "ArtworkColor", back_populates="artwork", cascade="all, delete-orphan"
    )
    tags: Mapped[list["ArtworkTag"]] = relationship(
        "ArtworkTag", back_populates="artwork", cascade="all, delete-orphan"
    )


class ArtworkColor(Base):
    __tablename__ = "artwork_colors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artwork_id: Mapped[str] = mapped_column(String, ForeignKey("artworks.id"))
    r: Mapped[int] = mapped_column(Integer)
    g: Mapped[int] = mapped_column(Integer)
    b: Mapped[int] = mapped_column(Integer)
    l_value: Mapped[float] = mapped_column(Float)
    a_value: Mapped[float] = mapped_column(Float)
    b_value: Mapped[float] = mapped_column(Float)
    percentage: Mapped[float] = mapped_column(Float)
    artwork: Mapped["Artwork"] = relationship("Artwork", back_populates="colors")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    artworks: Mapped[list["ArtworkTag"]] = relationship(
        "ArtworkTag", back_populates="tag", cascade="all, delete-orphan"
    )


class ArtworkTag(Base):
    __tablename__ = "artwork_tags"
    artwork_id: Mapped[str] = mapped_column(
        String, ForeignKey("artworks.id"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id"), primary_key=True
    )
    artwork: Mapped["Artwork"] = relationship("Artwork", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="artworks")
