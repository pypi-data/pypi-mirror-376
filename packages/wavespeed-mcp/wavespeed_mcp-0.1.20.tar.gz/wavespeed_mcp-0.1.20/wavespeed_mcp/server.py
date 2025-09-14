"""
WaveSpeed MCP Server

This server connects to WaveSpeed AI API endpoints which may involve costs.
Any tool that makes an API call is clearly marked with a cost warning.

Note: Always ensure you have proper API credentials before using these tools.
"""

import os
import requests
import time
import json
import logging
import asyncio
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions

from wavespeed_mcp.utils import (
    build_output_path,
    build_output_file,
    validate_loras,
    get_image_as_base64,
    process_image_input,
    is_english_text,
)
from wavespeed_mcp.const import (
    DEFAULT_IMAGE_SIZE,
    DEFAULT_NUM_INFERENCE_STEPS,
    DEFAULT_GUIDANCE_SCALE,
    DEFAULT_NUM_IMAGES,
    DEFAULT_SEED,
    DEFAULT_IMAGE_LORA,
    ENV_WAVESPEED_API_KEY,
    ENV_WAVESPEED_API_HOST,
    ENV_WAVESPEED_MCP_BASE_PATH,
    ENV_RESOURCE_MODE,
    RESOURCE_MODE_URL,
    RESOURCE_MODE_BASE64,
    DEFAULT_LOG_LEVEL,
    ENV_FASTMCP_LOG_LEVEL,
    API_VERSION,
    API_BASE_PATH,
    API_IMAGE_ENDPOINT,
    API_VIDEO_ENDPOINT,
    API_IMAGE_TO_IMAGE_ENDPOINT,
    ENV_API_TEXT_TO_IMAGE_ENDPOINT,
    ENV_API_IMAGE_TO_IMAGE_ENDPOINT,
    ENV_API_VIDEO_ENDPOINT,
)
from wavespeed_mcp.exceptions import (
    WavespeedRequestError,
    WavespeedAuthError,
    WavespeedTimeoutError,
)
from wavespeed_mcp.client import WavespeedAPIClient

# Load environment variables
load_dotenv()

# Configure logging

logging.basicConfig(
    level=os.getenv(ENV_FASTMCP_LOG_LEVEL, DEFAULT_LOG_LEVEL),
    format="%(asctime)s - wavespeed-mcp - %(levelname)s - %(message)s",
)
logger = logging.getLogger("wavespeed-mcp")

# Get configuration from environment variables
api_key = os.getenv(ENV_WAVESPEED_API_KEY)
api_host = os.getenv(ENV_WAVESPEED_API_HOST, "https://api.wavespeed.ai")
base_path = os.getenv(ENV_WAVESPEED_MCP_BASE_PATH) or "~/Desktop"
resource_mode = os.getenv(ENV_RESOURCE_MODE, RESOURCE_MODE_URL)

# Validate required environment variables
if not api_key:
    raise ValueError(f"{ENV_WAVESPEED_API_KEY} environment variable is required")

# Initialize MCP server and API client
server = Server("WaveSpeed")
api_client = WavespeedAPIClient(api_key, f"{api_host}{API_BASE_PATH}/{API_VERSION}")


class FileInfo(BaseModel):
    """Information about a local file."""

    path: str
    index: int


class Base64Info(BaseModel):
    """Information about a base64 encoded resource."""

    data: str
    mime_type: str
    index: int


class WaveSpeedResult(BaseModel):
    """Unified model for WaveSpeed generation results."""

    status: str = "success"
    urls: List[str] = []
    base64: List[Base64Info] = []
    local_files: List[FileInfo] = []
    error: Optional[str] = None
    processing_time: float = 0.0
    model: Optional[str] = None

    def to_json(self) -> str:
        """Convert the result to a JSON string."""
        return json.dumps(self.model_dump(), indent=2)


class LoraConfig(BaseModel):
    """Configuration for a single LoRA model."""

    path: str
    scale: float = 1.0




def _process_wavespeed_request(
    api_endpoint: str,
    payload: dict,
    output_directory: Optional[str],
    prompt: str,
    resource_type: str = "image",  # "image" or "video"
    operation_name: str = "Generation",
) -> TextContent:
    """Process a WaveSpeed API request and handle the response.

    This is a common function to handle API requests, polling for results,
    and processing the output based on the resource mode.

    Args:
        api_endpoint: The API endpoint to call
        payload: The request payload
        output_directory: Directory to save generated files
        prompt: The prompt used for generation
        resource_type: Type of resource being generated ("image" or "video")
        operation_name: Name of the operation for logging

    Returns:
        TextContent with the result JSON
    """

    begin_time = time.time()
    try:
        # Make API request
        response_data = api_client.post(api_endpoint, json=payload)
        request_id = response_data.get("data", {}).get("id")

        if not request_id:
            error_result = WaveSpeedResult(
                status="error",
                error="Failed to get request ID from response. Please try again.",
            )
            return TextContent(type="text", text=error_result.to_json())

        logger.info(f"{operation_name} request submitted with ID: {request_id}")

        # Poll for results
        result = api_client.poll_result(request_id)
        outputs = result.get("outputs", [])

        if not outputs:
            error_result = WaveSpeedResult(
                status="error",
                error=f"No {resource_type} outputs received. Please try again.",
            )
            return TextContent(type="text", text=error_result.to_json())

        end = time.time()
        processing_time = end - begin_time

        model = result.get("model", "")

        logger.info(f"{operation_name} completed in {processing_time:.2f} seconds")

        # Prepare result
        result = WaveSpeedResult(
            urls=outputs, processing_time=processing_time, model=model
        )

        # Handle different resource modes
        if resource_mode == RESOURCE_MODE_URL:
            # Only return URLs
            pass
        elif resource_mode == RESOURCE_MODE_BASE64:
            # Get base64 encoding
            if resource_type == "video":
                # For video, usually just one is returned
                video_url = outputs[0]
                try:
                    response = requests.get(video_url)
                    response.raise_for_status()

                    # Convert to base64
                    import base64

                    base64_data = base64.b64encode(response.content).decode("utf-8")

                    result.base64.append(
                        Base64Info(data=base64_data, mime_type="video/mp4", index=0)
                    )

                    logger.info(f"Successfully encoded {resource_type} to base64")
                except Exception as e:
                    logger.error(f"Failed to encode {resource_type}: {str(e)}")
            else:
                # For images, handle multiple outputs
                for i, url in enumerate(outputs):
                    try:
                        # Get base64 encoding and MIME type
                        base64_data, mime_type = get_image_as_base64(url)
                        result.base64.append(
                            Base64Info(data=base64_data, mime_type=mime_type, index=i)
                        )
                        logger.info(
                            f"Successfully encoded {resource_type} {i+1}/{len(outputs)} to base64"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to encode {resource_type} {i+1}: {str(e)}"
                        )
        else:
            # Save to local file
            output_path = build_output_path(output_directory, base_path)
            output_path.mkdir(parents=True, exist_ok=True)

            if resource_type == "video":
                # For video, usually just one is returned
                video_url = outputs[0]
                try:
                    filename = build_output_file(
                        resource_type, prompt, output_path, "mp4"
                    )

                    response = requests.get(video_url, stream=True)
                    response.raise_for_status()

                    with open(filename, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    result.local_files.append(FileInfo(path=str(filename), index=0))
                    logger.info(f"Successfully saved {resource_type} to {filename}")
                except Exception as e:
                    logger.error(f"Failed to save {resource_type}: {str(e)}")
            else:
                # For images, handle multiple outputs
                for i, url in enumerate(outputs):
                    try:
                        output_file_name = build_output_file(
                            resource_type, f"{i}_{prompt}", output_path, "jpeg"
                        )

                        response = requests.get(url)
                        response.raise_for_status()

                        with open(output_file_name, "wb") as f:
                            f.write(response.content)

                        result.local_files.append(
                            FileInfo(path=str(output_file_name), index=i)
                        )
                        logger.info(
                            f"Successfully saved {resource_type} {i+1}/{len(outputs)} to {output_file_name}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to save {resource_type} {i+1}: {str(e)}")

        # Return unified JSON structure
        return TextContent(type="text", text=result.to_json())

    except (WavespeedAuthError, WavespeedRequestError, WavespeedTimeoutError) as e:
        logger.error(f"{operation_name} failed: {str(e)}")
        error_result = WaveSpeedResult(
            status="error", error=f"Failed to generate {resource_type}: {str(e)}"
        )
        return TextContent(type="text", text=error_result.to_json())
    except Exception as e:
        logger.exception(f"Unexpected error during {operation_name.lower()}: {str(e)}")
        error_result = WaveSpeedResult(
            status="error", error=f"An unexpected error occurred: {str(e)}"
        )
        return TextContent(type="text", text=error_result.to_json())


def get_models(model):
    if model == "" or model is None:
        model = os.getenv(ENV_API_TEXT_TO_IMAGE_ENDPOINT, API_IMAGE_ENDPOINT)

    if not model.startswith("/"):
        model = "/" + model

    return model


def get_image_models(model):
    if model == "" or model is None:
        model = os.getenv(ENV_API_IMAGE_TO_IMAGE_ENDPOINT, API_IMAGE_TO_IMAGE_ENDPOINT)

    if not model.startswith("/"):
        model = "/" + model

    return model


def get_video_models(model):
    if model == "" or model is None:
        model = os.getenv(ENV_API_VIDEO_ENDPOINT, API_VIDEO_ENDPOINT)

    if not model.startswith("/"):
        model = "/" + model

    return model


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="text_to_image",
            description="Generate an image from text prompt using WaveSpeed AI. Prompt MUST BE IN ENGLISH.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the image to generate. MUST BE IN ENGLISH."
                    },
                    "model": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Model to use for image generation",
                        "default": None
                    },
                    "loras": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "scale": {"type": "number", "default": 1.0}
                                    },
                                    "required": ["path"],
                                    "additionalProperties": False
                                }
                            },
                            {"type": "null"}
                        ],
                        "description": "List of LoRA models to use",
                        "default": None
                    },
                    "size": {
                        "type": "string",
                        "description": "Size of the output image in format 'width*height'",
                        "default": "1024*1024"
                    },
                    "num_inference_steps": {
                        "type": "integer",
                        "description": "Number of denoising steps",
                        "default": 28
                    },
                    "guidance_scale": {
                        "type": "number",
                        "description": "Guidance scale for text adherence",
                        "default": 3.5
                    },
                    "num_images": {
                        "type": "integer",
                        "description": "Number of images to generate",
                        "default": 1
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed for reproducible results",
                        "default": -1
                    },
                    "enable_safety_checker": {
                        "type": "boolean",
                        "description": "Whether to enable safety filtering",
                        "default": True
                    },
                    "output_directory": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Directory to save the generated images",
                        "default": None
                    }
                },
                "required": ["prompt"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="image_to_image",
            description="Generate an image from an existing image using WaveSpeed AI. Prompt MUST BE IN ENGLISH.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "description": "URL, base64 string, or local file path of the input image to modify"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the desired modifications. MUST BE IN ENGLISH."
                    },
                    "images": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            {"type": "null"}
                        ],
                        "description": "List of URLs to images to modify",
                        "default": None
                    },
                    "model": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Model to use for image generation",
                        "default": None
                    },
                    "guidance_scale": {
                        "type": "number",
                        "description": "Guidance scale for text adherence",
                        "default": 3.5
                    },
                    "enable_safety_checker": {
                        "type": "boolean",
                        "description": "Whether to enable safety filtering",
                        "default": True
                    },
                    "output_directory": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Directory to save the generated images",
                        "default": None
                    }
                },
                "required": ["image", "prompt"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="generate_video",
            description="Generate a video using WaveSpeed AI. Prompt MUST BE IN ENGLISH.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "description": "URL, base64 string, or local file path of the input image to animate"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the video to generate. MUST BE IN ENGLISH."
                    },
                    "model": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Model to use for video generation",
                        "default": None
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "Text description of what to avoid in the video",
                        "default": ""
                    },
                    "loras": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "scale": {"type": "number", "default": 1.0}
                                    },
                                    "required": ["path"],
                                    "additionalProperties": False
                                }
                            },
                            {"type": "null"}
                        ],
                        "description": "List of LoRA models to use",
                        "default": None
                    },
                    "size": {
                        "type": "string",
                        "description": "Size of the output video in format 'width*height'",
                        "default": "832*480"
                    },
                    "num_inference_steps": {
                        "type": "integer",
                        "description": "Number of denoising steps",
                        "default": 30
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration of the video in seconds. Must be 5 or 10.",
                        "enum": [5, 10],
                        "default": 5
                    },
                    "guidance_scale": {
                        "type": "number",
                        "description": "Guidance scale for text adherence",
                        "default": 5
                    },
                    "flow_shift": {
                        "type": "integer",
                        "description": "Shift of the flow in the video",
                        "default": 3
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed for reproducible results",
                        "default": -1
                    },
                    "enable_safety_checker": {
                        "type": "boolean",
                        "description": "Whether to enable safety filtering",
                        "default": True
                    },
                    "output_directory": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Directory to save the generated video",
                        "default": None
                    }
                },
                "required": ["image", "prompt"],
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "text_to_image":
        return [await text_to_image_impl(**arguments)]
    elif name == "image_to_image":
        return [await image_to_image_impl(**arguments)]
    elif name == "generate_video":
        return [await generate_video_impl(**arguments)]
    else:
        raise ValueError(f"Unknown tool: {name}")


async def text_to_image_impl(

    prompt: str,
    model: Optional[str] = None,
    loras: Optional[List[dict]] = None,
    size: str = DEFAULT_IMAGE_SIZE,
    num_inference_steps: int = DEFAULT_NUM_INFERENCE_STEPS,
    guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
    num_images: int = DEFAULT_NUM_IMAGES,
    seed: int = DEFAULT_SEED,
    enable_safety_checker: bool = True,
    output_directory: Optional[str] = None,
) -> TextContent:
    """Generate an image from text prompt using WaveSpeed AI."""

    if not prompt:
        error_result = WaveSpeedResult(
            status="error",
            error="Prompt is required for image generation. Please provide an English prompt for optimal results.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # Check if prompt is in English
    if not is_english_text(prompt):
        error_result = WaveSpeedResult(
            status="error",
            error="Prompt must be in English. Please provide an English prompt for optimal results.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # Validate and set default loras if not provided
    if not loras:
        loras_dicts = [DEFAULT_IMAGE_LORA]
    else:
        loras_dicts = validate_loras(loras)

    # Prepare API payload
    payload = {
        "prompt": prompt,
        "loras": loras_dicts,
        "size": size,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
        "num_images": num_images,
        "max_images": num_images,
        "seed": seed,
        "enable_base64_output": False,  # 使用URL，后续自己转换为base64
        "enable_safety_checker": enable_safety_checker,
    }

    return _process_wavespeed_request(
        api_endpoint=get_models(model),
        payload=payload,
        output_directory=output_directory,
        prompt=prompt,
        resource_type="image",
        operation_name="Image generation",
    )


async def image_to_image_impl(
    image: str,
    prompt: str,
    images: Optional[List[str]] = None,
    model: Optional[str] = None,
    guidance_scale: float = 3.5,
    enable_safety_checker: bool = True,
    output_directory: Optional[str] = None,
) -> TextContent:
    """Generate an image from an existing image using WaveSpeed AI."""

    if not image and not images:
        error_result = WaveSpeedResult(
            status="error",
            error="Input image(s) required for image-to-image generation. Provide either 'image' or 'images' parameter.",
        )
        return TextContent(type="text", text=error_result.to_json())

    if not prompt:
        error_result = WaveSpeedResult(
            status="error",
            error="Prompt is required for image-to-image generation. Please provide an English prompt for optimal results.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # Check if prompt is in English
    if not is_english_text(prompt):
        error_result = WaveSpeedResult(
            status="error",
            error="Prompt must be in English. Please provide an English prompt for optimal results.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # handle image input(s)
    payload = {
        "prompt": prompt,
        "guidance_scale": guidance_scale,
        "enable_safety_checker": enable_safety_checker,
    }

    try:
        # Process single image if provided
        if image:
            processed_image = process_image_input(image)
            payload["image"] = processed_image
            logger.info("Successfully processed single input image")

        # Process multiple images if provided
        if images:
            processed_images = []
            for img in images:
                processed_img = process_image_input(img)
                processed_images.append(processed_img)
            payload["images"] = processed_images
            logger.info(f"Successfully processed {len(processed_images)} input images")

        if not image:
            image = images[0]
            payload["image"] = image

        if not images:
            images = [image]
            payload["images"] = images

    except Exception as e:
        logger.error(f"Failed to process input image(s): {str(e)}")
        error_result = WaveSpeedResult(
            status="error", error=f"Failed to process input image(s): {str(e)}"
        )
        return TextContent(type="text", text=error_result.to_json())

    return _process_wavespeed_request(
        api_endpoint=get_image_models(model),
        payload=payload,
        output_directory=output_directory,
        prompt=prompt,
        resource_type="image",
        operation_name="Image-to-image generation",
    )


async def generate_video_impl(
    image: str,
    prompt: str,
    model: Optional[str] = None,
    negative_prompt: str = "",
    loras: Optional[List[dict]] = None,
    size: str = "832*480",
    num_inference_steps: int = 30,
    duration: int = 5,
    guidance_scale: float = 5,
    flow_shift: int = 3,
    seed: int = -1,
    enable_safety_checker: bool = True,
    output_directory: Optional[str] = None,
) -> TextContent:
    """Generate a video using WaveSpeed AI."""

    if not image:
        error_result = WaveSpeedResult(
            status="error",
            error="Input image is required for video generation. Can use generate_image tool to generate an image first.",
        )
        return TextContent(type="text", text=error_result.to_json())

    if not prompt:
        error_result = WaveSpeedResult(
            status="error",
            error="Prompt is required for video generation. Please provide an English prompt for optimal results.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # Check if prompt is in English
    if not is_english_text(prompt):
        error_result = WaveSpeedResult(
            status="error",
            error="Prompt must be in English. Please provide an English prompt for optimal results.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # Validate and set default loras if not provided
    if not loras:
        loras_dicts: List[Dict[str, Union[str, float]]] = []
    else:
        loras_dicts = validate_loras(loras)

    if duration not in [5, 10]:
        error_result = WaveSpeedResult(
            status="error",
            error="Duration must be 5 or 10 seconds. Please set it to 5 or 10.",
        )
        return TextContent(type="text", text=error_result.to_json())

    # handle image input
    try:
        processed_image = process_image_input(image)
        logger.info("Successfully processed input image")
    except Exception as e:
        logger.error(f"Failed to process input image: {str(e)}")
        error_result = WaveSpeedResult(
            status="error", error=f"Failed to process input image: {str(e)}"
        )
        return TextContent(type="text", text=error_result.to_json())

    # Prepare API payload
    payload = {
        "image": processed_image,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "loras": loras_dicts,
        "size": size,
        "num_inference_steps": num_inference_steps,
        "duration": duration,
        "guidance_scale": guidance_scale,
        "flow_shift": flow_shift,
        "seed": seed,
        "enable_safety_checker": enable_safety_checker,
    }

    return _process_wavespeed_request(
        api_endpoint=get_video_models(model),
        payload=payload,
        output_directory=output_directory,
        prompt=prompt,
        resource_type="video",
        operation_name="Video generation",
    )


def main():
    """Run the WaveSpeed MCP server"""
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="WaveSpeed",
                    server_version="0.1.18"
                )
            )
    
    print("Starting WaveSpeed MCP server")
    asyncio.run(run_server())



if __name__ == "__main__":
    main()
