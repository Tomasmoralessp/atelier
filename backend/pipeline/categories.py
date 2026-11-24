import enum


class ImageType(enum.Enum):
    photograph = "photograph"
    painting = "painting"
    drawing = "drawing"
    illustration = "illustration"
    comic_art = "comic_art"
    graphic_design = "graphic_design"
    logo = "logo"
    product_design = "product_design"


IMAGE_TYPE_PROMPTS = {
    ImageType.photograph: [
        "a real photograph taken with a camera",
        "a photo capturing a real scene",
    ],
    ImageType.painting: ["a painting", "a traditional painting"],
    ImageType.drawing: ["a drawing", "a hand-drawn sketch"],
    ImageType.illustration: ["a digital illustration"],
    ImageType.comic_art: ["comic book art"],
    ImageType.graphic_design: ["a graphic design piece"],
    ImageType.logo: ["a logo design"],
    ImageType.product_design: ["product packaging design"],
}


class Subject(enum.Enum):
    landscape = "landscape"
    person = "person"
    animal = "animal"
    abstract = "abstract"
    object = "object"


SUBJECT_PROMPTS = {
    Subject.landscape: [
        "a landscape or scenic view",
        "a wide view of a place, whether natural or urban",
    ],
    Subject.person: ["an image of a person", "an image of many people"],
    Subject.animal: ["an image of an animal", "an image of many animals"],
    Subject.abstract: [
        "an image with no recognizable people, animals, or objects, just shapes and colors"
    ],
    Subject.object: ["an image of objects, with no people"],
}


class ArtTechnique(enum.Enum):
    watercolor = "watercolor"
    oil = "oil"
    acrylic = "acrylic"
    pencil_sketch = "pencil_sketch"
    ink = "ink"
    collage = "collage"
    vector_art = "vector_art"


ART_TECHNIQUE_PROMPTS = {
    ArtTechnique.watercolor: ["a watercolor painting"],
    ArtTechnique.oil: ["an oil painting"],
    ArtTechnique.acrylic: ["an acrylic painting"],
    ArtTechnique.pencil_sketch: ["a pencil sketch"],
    ArtTechnique.ink: ["an ink drawing"],
    ArtTechnique.collage: ["a collage artwork"],
    ArtTechnique.vector_art: ["vector illustration"],
}

TYPES_WITH_SUBJECT = {
    ImageType.photograph.name,
    ImageType.painting.name,
    ImageType.drawing.name,
    ImageType.illustration.name,
    ImageType.comic_art.name,
}


TYPES_WITH_TECHNIQUE = {
    ImageType.painting.name,
    ImageType.drawing.name,
    ImageType.illustration.name,
    ImageType.comic_art.name,
}

TECHNIQUE_PROMPTS_BY_TYPE = {
    ImageType.photograph: None,
    ImageType.painting: ART_TECHNIQUE_PROMPTS,
    ImageType.drawing: ART_TECHNIQUE_PROMPTS,
    ImageType.illustration: ART_TECHNIQUE_PROMPTS,
    ImageType.comic_art: ART_TECHNIQUE_PROMPTS,
    ImageType.graphic_design: None,
    ImageType.logo: None,
    ImageType.product_design: None,
}
