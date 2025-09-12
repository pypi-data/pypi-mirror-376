"""Main Entry Point for the Image Format Converter MCP Server."""

from .general_conversion import auto_convert_image, auto_convert_folder
from .gif_conversion import convert_images_to_gif
from .pdf_conversion import convert_images_to_pdf

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp import McpError  # Import McpError for proper error handling
import gc
import sys
from typing import Union, Dict, Any

mcp = FastMCP("image-format-converter-mcp")


def ok(msg: str) -> Union[TextContent, list]:
    """Create a Success Response."""
    # FastMCP expects either TextContent or list of content items
    # When returning success, we should NOT set any error flags
    return TextContent(type="text", text=msg)


def error(msg: str) -> None:
    """Raise an Error - FastMCP will handle the error propagation."""
    # Use McpError for proper error handling
    raise McpError(msg)


def isError(result: Any) -> bool:
    """Check if a result represents an error condition.
    
    Args:
        result: The result to check (could be exception, error message, None, etc.)
    
    Returns:
        bool: True if result represents an error, False otherwise
    """
    if result is None:
        return True
    
    if isinstance(result, Exception):
        return True
    
    if isinstance(result, str):
        error_indicators = ['error', 'failed', 'exception', 'invalid', 'not found', 'cannot']
        return any(indicator in result.lower() for indicator in error_indicators)
    
    if isinstance(result, dict) and 'error' in result:
        return True
        
    return False


@mcp.tool("auto_convert_image", description="Converts a single image to a specified format (jpeg, png, webp, heic, avif, bmp, tiff, ico) and saves the converted image to the output directory if provided, otherwise same location as input. Args: input_dir (str) = absolute path to source image file || target_format (str) = desired output format (jpeg, png, webp, heic, avif, bmp, tiff, ico) || output_dir (str)(optional): optional output directory path (without filename), defaults to same directory as input file || file_name (str)(optional) = optional custom filename, defaults to auto naming.")
def auto_convert_image_tool(input_dir: str, target_format: str, output_dir: str = None, file_name: str = None) -> TextContent:
    """Convert a Single Image to Target Format."""
    try:
        # First validate inputs before capturing output
        from pathlib import Path
        input_path = Path(input_dir)
        if not input_path.exists():
            raise McpError(
                f"Failed to Convert Image: Input file does not exist: {input_dir}",
                meta={"input_dir": input_dir, "target_format": target_format}
            )
        if not input_path.is_file():
            raise McpError(
                f"Failed to Convert Image: Input path is not a file: {input_dir}",
                meta={"input_dir": input_dir, "target_format": target_format}
            )
        
        # Capture stdout/stderr to Collect Warnings
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
            result = auto_convert_image(input_dir, target_format, output_dir, file_name)
        
        # Check if There Were Warnings
        output_text = output_buffer.getvalue()
        warnings = []
        if "(WARNING)" in output_text:
            warnings = [line.strip() for line in output_text.split('\n') if "(WARNING)" in line]
        
        if warnings:
            return ok(f"Successfully converted image to: {result}\n\n(WARNING) Warnings:\n" + "\n".join(warnings))
        else:
            return ok(f"Successfully converted image to: {result}")
            
    except McpError:
        # Re-raise McpError as is
        raise
    except Exception as e:
        # Convert any other exception to McpError
        error_msg = f"Failed to Convert Image: {str(e)}"
        print(f"ERROR: {error_msg}", file=sys.stderr)  # Debug logging
        raise McpError(
            error_msg,
            meta={"input_dir": input_dir, "target_format": target_format}
        )
    finally:
        # Simple Memory Cleanup
        gc.collect()


@mcp.tool("auto_convert_folder", description="Converts all images in the input folder to a specified format (jpeg, png, webp, heic, avif, bmp, tiff, ico). Saves the converted images in a new subfolder inside the input folder. Args: input_dir (str) = absolute path to input folder || target_format (str) = desired output format (jpeg, png, webp, heic, avif, bmp, tiff, ico).")
def auto_convert_folder_tool(input_dir: str, target_format: str) -> TextContent:
    """Convert All Images in a Folder to Target Format."""
    try:
        # First validate inputs before processing
        from pathlib import Path
        input_path = Path(input_dir)
        if not input_path.exists():
            raise McpError(
                f"Failed to Convert Folder: Input folder does not exist: {input_dir}",
                meta={"input_dir": input_dir, "target_format": target_format}
            )
        if not input_path.is_dir():
            raise McpError(
                f"Failed to Convert Folder: Input path is not a directory: {input_dir}",
                meta={"input_dir": input_dir, "target_format": target_format}
            )
        
        result = auto_convert_folder(input_dir, target_format)
        return ok(f"Successfully converted folder. Output: {result}")
        
    except McpError:
        # Re-raise McpError as is
        raise
    except Exception as e:
        # Convert any other exception to McpError
        raise McpError(
            f"Failed to Convert Folder: {str(e)}",
            meta={"input_dir": input_dir, "target_format": target_format}
        )
    finally:
        # Simple Memory Cleanup
        gc.collect()


@mcp.tool("convert_images_to_gif", description="Creates a GIF by combining all supported images (jpeg, png, webp, heic, avif, bmp, tiff, ico) found in the input folder and saves the GIF to the output directory if provided, otherwise same location as input. Args: input_dir (str) = absolute path to input folder || output_dir (str)(optional): optional output directory path (without filename), defaults to input folder || file_name (str)(optional) = optional custom filename, defaults to auto naming || duration (int)(optional) = optional duration per frame via milliseconds (accept 1-10,000ms), defaults to 100 || loop (int)(optional) = optional number of playback loops (0 = infinite), defaults to 0 || color_mode (str)(optional) = optional between 'RGB' (full color), 'P' (indexed color) or 'L' (grayscale), defaults to 'RGB' || color_count (int)(optional) = optional number of colors (accept 2-256) for 'P' and 'L' color modes (ignored for 'RGB'), defaults to 256 || brightness (float)(optional) = optional between 0.0 (darkest) to 5.0 (brightest), defaults to 1.0 || contrast (float)(optional) = optional between 0.0 (least) to 5.0 (most), defaults to 1.0 || saturation (float)(optional) = optional between 0.0 (least) to 5.0 (most), defaults to 1.0 || ping_pong (bool)(optional) = optional playback loop via forward→backward→forward, defaults to False || easing (str)(optional) = optional easing curve between 'none', 'ease-in', 'ease-out' and 'ease-in-out', defaults to 'none' || easing_strength (float)(optional) = optional easing intensity between 0.1 (subtle) to 5.0 (strong), defaults to 1.0 || size_strategy (str)(optional) = optional size unification strategy between 'auto' (keep original), 'min_size' (use smallest), 'max_size' (use largest), 'custom' (specify dimensions), defaults to 'auto' || resize_mode (str)(optional) = optional resize behavior between 'fit' (preserve aspect ratio with padding), 'fill' (crop to fill), 'stretch' (distort to fit), defaults to 'fit' || alignment (str)(optional) = optional position for fit/fill modes between 'center', 'top_left', 'top_right', 'bottom_left', 'bottom_right', defaults to 'center' || target_width (int)(optional) = optional width for custom size strategy || target_height (int)(optional) = optional height for custom size strategy || background_color (str)(optional) = optional background color for fit mode (CSS color names or hex), defaults to 'black'.")
def convert_images_to_gif_tool(
    input_dir: str,
    file_name: str = None,
    output_dir: str = None,
    duration: int = 100,
    loop: int = 0,
    color_mode: str = "RGB",
    color_count: int = 256,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    ping_pong: bool = False,
    easing: str = "none",
    easing_strength: float = 1.0,
    size_strategy: str = "auto",
    resize_mode: str = "fit",
    alignment: str = "center", 
    target_width: int = None,
    target_height: int = None,
    background_color: str = "black"
) -> TextContent:
    """Convert Multiple Images to Animated GIF."""
    try:
        # First validate inputs before processing
        from pathlib import Path
        input_path = Path(input_dir)
        if not input_path.exists():
            raise McpError(
                f"Failed to Create GIF: Input folder does not exist: {input_dir}",
                meta={"input_dir": input_dir, "duration": duration, "color_mode": color_mode}
            )
        if not input_path.is_dir():
            raise McpError(
                f"Failed to Create GIF: Input path is not a directory: {input_dir}",
                meta={"input_dir": input_dir, "duration": duration, "color_mode": color_mode}
            )
        
        # Capture stdout/stderr to Collect Warnings
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
            result = convert_images_to_gif(
                input_dir, file_name, output_dir, duration, loop, color_mode, color_count,
                brightness, contrast, saturation, ping_pong, easing, easing_strength,
                size_strategy, resize_mode, alignment, target_width, target_height, background_color
            )
        
        # Check if There Were Warnings
        output_text = output_buffer.getvalue()
        warnings = []
        if "(WARNING)" in output_text:
            warnings = [line.strip() for line in output_text.split('\n') if "(WARNING)" in line]
        
        if warnings:
            return ok(f"Successfully created GIF: {result}\n\n(WARNING) Warnings:\n" + "\n".join(warnings))
        else:
            return ok(f"Successfully created GIF: {result}")
            
    except McpError:
        # Re-raise McpError as is
        raise
    except Exception as e:
        # Convert any other exception to McpError  
        raise McpError(
            f"Failed to Create GIF: {str(e)}",
            meta={
                "input_dir": input_dir,
                "duration": duration,
                "color_mode": color_mode
            }
        )
    finally:
        # Simple Memory Cleanup
        gc.collect()


@mcp.tool("convert_images_to_pdf", description="Creates a PDF by combining all supported images (jpeg, png, webp, heic, avif, bmp, tiff, ico), one image per PDF page, found in the input folder and saves the PDF to the output directory if provided, otherwise same location as input. Args: input_dir (str) = absolute path to input folder || output_dir (str)(optional) = optional output directory path (without filename), defaults to input folder || file_name (str)(optional) = optional custom filename, defaults to auto naming || sort_order (str)(optional) = optional image file combination (page) order between 'alphabetical' (a-z & 0-9), 'creation_time' (latest-earliest), 'modification_time' (latest-earliest), defaults to 'alphabetical' || page_size (str)(optional) = optional PDF page size between A3/A4/A5/B3/B4/B5/Letter/Legal/Executive/Tabloid/16:9/4:3/Square, defaults to 'A4' || dpi (int)(optional) = optional PDF resolution (accept 72-1200), defaults to 300 || fit_to_page (bool)(optional) = optional scale images to exactly fit PDF pages, defaults to True || center_image (bool)(optional) = optional center images on PDF pages, defaults to True || background_color (str)(optional) = optional background color between 'white', 'light gray', 'gray', 'dark gray', 'black', 'light red', 'red', 'dark red', 'yellow', 'orange', 'lime', 'light green', 'green', 'dark green', 'light blue', 'blue', 'dark blue', 'light purple', 'purple', 'dark purple', 'light pink', 'pink', 'dark pink', 'light brown', 'brown', 'dark brown', defaults to 'white'.")
def convert_images_to_pdf_tool(
    input_dir: str,
    output_dir: str = None,
    file_name: str = None,
    sort_order: str = "alphabetical",
    page_size: str = "A4",
    dpi: int = 300,
    fit_to_page: bool = True,
    center_image: bool = True,
    background_color: str = "white"
) -> TextContent:
    """Combine Multiple Images into PDF."""
    try:
        # First validate inputs before processing
        from pathlib import Path
        input_path = Path(input_dir)
        if not input_path.exists():
            raise McpError(
                f"Failed to Create PDF: Input folder does not exist: {input_dir}",
                meta={"input_dir": input_dir, "page_size": page_size, "dpi": dpi}
            )
        if not input_path.is_dir():
            raise McpError(
                f"Failed to Create PDF: Input path is not a directory: {input_dir}",
                meta={"input_dir": input_dir, "page_size": page_size, "dpi": dpi}
            )
        
        # Capture stdout/stderr to Collect Warnings
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
            result = convert_images_to_pdf(
                input_dir, output_dir, file_name, sort_order, page_size,
                dpi, fit_to_page, center_image, background_color
            )
        
        # Check if There Were Warnings
        output_text = output_buffer.getvalue()
        warnings = []
        if "(WARNING)" in output_text:
            warnings = [line.strip() for line in output_text.split('\n') if "(WARNING)" in line]
        
        if warnings:
            return ok(f"Successfully created PDF: {result}\n\n(WARNING) Warnings:\n" + "\n".join(warnings))
        else:
            return ok(f"Successfully created PDF: {result}")
            
    except McpError:
        # Re-raise McpError as is
        raise
    except Exception as e:
        # Convert any other exception to McpError
        raise McpError(
            f"Failed to Create PDF: {str(e)}",
            meta={
                "input_dir": input_dir,
                "page_size": page_size,
                "dpi": dpi
            }
        )
    finally:
        # Simple Memory Cleanup
        gc.collect()


def main():
    """Run the MCP Server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
