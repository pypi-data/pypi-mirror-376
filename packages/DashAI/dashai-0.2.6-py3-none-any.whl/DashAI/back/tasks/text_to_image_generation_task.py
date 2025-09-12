import os
import uuid
from typing import Any, List, Tuple

from PIL import Image

from DashAI.back.dependencies.database.models import ProcessData
from DashAI.back.tasks.base_generative_task import BaseGenerativeTask


class TextToImageGenerationTask(BaseGenerativeTask):
    """Base class for image generation tasks.

    Here you can change the methods provided by class Task.
    """

    metadata: dict = {
        "inputs_types": [str],
        "outputs_types": [Image.Image],
        "inputs_cardinality": 1,
        "outputs_cardinality": "n",
    }
    DISPLAY_NAME: str = "Text to Image Generation"
    DESCRIPTION: str = "This task generates images based on the provided input text."

    def prepare_for_task(
        self,
        input: List[ProcessData],
        **kwargs: Any,
    ) -> str:
        """Change the inputs to suit the image generation task.

        Parameters
        ----------
        inputs : str
            Input to be changed

        Returns
        -------
        str
            Input with the new types
        """
        return str(input[0].data)

    def prepare_input_for_database(
        self,
        input: List[str],
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Prepare the input for the database.

        Parameters
        ----------
        input : str
            Input to be changed

        Returns
        -------
        List[Tuple[str, str]]
            Input with the new types as a list of tuples containing the data
            and its type

        """
        return [(input[0], "str")]

    def process_output(
        self,
        output: List[Any],
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        """Process the output of a generative model.

        Parameters
        ----------
        output : List[Any]
            list of images to be processed

        Returns
        -------
        List[Tuple[str, str]]
            Processed output data as a list of tuples containing the data and its type
        """
        save_dir = kwargs.get("images_path")

        if not save_dir.exists():
            save_dir.mkdir(parents=True)

        image_paths = []

        for img in output:
            # Generate a unique file name
            file_name = str(uuid.uuid4())

            image_path = f"{file_name}.png"

            # Save the image
            img.save(save_dir / image_path, format="PNG")

            image_paths.append((str(image_path), "Image"))

        return image_paths

    def process_output_from_database(
        self,
        output: List[ProcessData],
        **kwargs: Any,
    ) -> List[ProcessData]:
        """Process the output of an image generation model from the database.

        Parameters
        ----------
        output : List[str]
            List of paths to the images

        Returns
        -------
        List[str]
            List of base64 encoded images
        """

        for op in output:
            op.data = os.path.basename(op.data)

        return output

    def process_input_from_database(
        self,
        input: List[ProcessData],
        **kwargs: Any,
    ) -> List[ProcessData]:
        """Process the input of an image generation model from the database.

        Parameters
        ----------
        input : List[str]
            List of prompts

        Returns
        -------
        List[str]
            List of prompts
        """
        return input
