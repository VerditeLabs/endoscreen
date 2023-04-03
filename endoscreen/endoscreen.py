"""Welcome to Pynecone! This file outlines the steps to create a basic app."""
from pcconfig import config
from typing import Any
import pynecone as pc


class State(pc.State):
    """The app state."""
    pass

class Camera(pc.Component):
    library = "react-camera-pro"
    tag = "Camera"
    #camera: pc.Var
    image: pc.Var[str]  # base64 encoded image

    @classmethod
    def get_controlled_triggers(cls) -> dict[str, pc.Var]:
        return {"on_click": pc.EVENT_ARG}

class CameraState(pc.State):
    #camera: Any = None
    image: str = ""


def index() -> pc.Component:
    return pc.center(
        pc.text("asdf"),
        Camera.create(on_click=CameraState.set_image),
        pc.text("asdf"),
        pc.Image(src=CameraState.image)

    )


# Add state and page to the app.
app = pc.App(state=State)
app.add_page(index)
app.compile()
