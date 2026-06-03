import os
import sys
import json
import urllib.request
import urllib.error
import mimetypes
import uuid
import argparse
from pathlib import Path

# Load dotenv helper if present, but don't hard-fail if not
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_env_vars():
    # Read custom environment variables with fallbacks
    base_url = os.environ.get("DOCUMENT_ILLUSTRATOR_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ.get("DOCUMENT_ILLUSTRATOR_API_KEY")
    model_name = os.environ.get("DOCUMENT_ILLUSTRATOR_MODEL_NAME", "dall-e-3")
    
    # Try looking in .env files if key not in environment
    if not api_key:
        # Search current directory and up to git root/parent
        curr_dir = Path.cwd()
        for parent in [curr_dir] + list(curr_dir.parents):
            env_path = parent / ".env"
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k == "DOCUMENT_ILLUSTRATOR_API_KEY":
                                api_key = v
                            elif k == "DOCUMENT_ILLUSTRATOR_BASE_URL":
                                base_url = v.rstrip("/")
                            elif k == "DOCUMENT_ILLUSTRATOR_MODEL_NAME":
                                model_name = v
                if api_key:
                    break
                    
    return base_url, api_key, model_name

def encode_multipart_formdata(fields, files):
    """
    fields: dict of name: value
    files: dict of name: (filename, path_or_bytes)
    Returns: body (bytes), headers (dict)
    """
    boundary = f"Boundary-{uuid.uuid4().hex}"
    CRLF = b"\r\n"
    L = []
    
    for key, value in fields.items():
        if value is None:
            continue
        L.append(f"--{boundary}".encode("utf-8"))
        L.append(f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"))
        L.append(b"")
        L.append(str(value).encode("utf-8"))
        
    for key, file_info in files.items():
        if not file_info:
            continue
        filename, data_or_path = file_info
        if isinstance(data_or_path, (str, Path)):
            with open(data_or_path, "rb") as f:
                file_content = f.read()
        else:
            file_content = data_or_path
            
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        
        L.append(f"--{boundary}".encode("utf-8"))
        L.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode("utf-8"))
        L.append(f"Content-Type: {mimetype}".encode("utf-8"))
        L.append(b"")
        L.append(file_content)
        
    L.append(f"--{boundary}--".encode("utf-8"))
    L.append(b"")
    
    body = CRLF.join(L)
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body))
    }
    return body, headers

def download_image(url, output_path):
    print(f"Downloading generated image from {url}...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req) as response:
        with open(output_path, "wb") as f:
            f.write(response.read())
    print(f"Saved to {output_path}")

def call_openai_compatible_api(mode, prompt, image_path, mask_path, size, output_path, model, output_format=None, extra_body_str=None):
    base_url, api_key, env_model = get_env_vars()
    
    if not api_key:
        print("[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
              "1. ERROR: DOCUMENT_ILLUSTRATOR_API_KEY environment variable is not set.\n"
              "2. ACTION: Add it to your .env file or system environment.\n"
              "3. FALLBACK: Fall back to the Agent Native engine (call generate_image tool) or the SVG Vector Diagram Engine.", file=sys.stderr)
        sys.exit(1)
        
    chosen_model = model if model else env_model
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Universal-Document-Illustrator/1.0"
    }
    
    # Parse extra_body if provided
    extra_body = {}
    if extra_body_str:
        try:
            extra_body = json.loads(extra_body_str)
        except Exception:
            try:
                import re
                import ast
                # Clean up common Windows shell quote-stripping issues (e.g. {watermark: false} -> {"watermark": False})
                cleaned = extra_body_str.strip()
                cleaned = re.sub(r'([a-zA-Z_]\w*)\s*:', r'"\1":', cleaned)
                cleaned = re.sub(r'\bfalse\b', 'False', cleaned)
                cleaned = re.sub(r'\btrue\b', 'True', cleaned)
                cleaned = re.sub(r'\bnull\b', 'None', cleaned)
                extra_body = ast.literal_eval(cleaned)
            except Exception as e:
                print(f"Warning: Failed to parse --extra-body: {e}")
            
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if mode == "generate":
            url = f"{base_url}/images/generations"
            data = {
                "prompt": prompt,
                "model": chosen_model,
                "n": 1,
                "size": size,
                "response_format": "url"
            }
            if output_format:
                data["output_format"] = output_format
            
            if image_path:
                import base64
                if not os.path.exists(image_path):
                    print(f"Error: Base image file '{image_path}' not found.")
                    sys.exit(1)
                ext = os.path.splitext(image_path)[1].lower().replace(".", "")
                if not ext:
                    ext = "png"
                elif ext == "jpg":
                    ext = "jpeg"
                print(f"Encoding reference image '{image_path}' to base64...")
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                base64_uri = f"data:image/{ext};base64,{encoded_string}"
                # Volcano Seedream standard is passing a list of base64 strings under "image"
                data["image"] = [base64_uri]
                
            data.update(extra_body)
            
            req_body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
            
            print(f"Calling: {url}")
            print(f"Prompt: {prompt}")
            print(f"Model: {chosen_model}")
            # Truncate base64 in log to keep it clean
            log_data = data.copy()
            if "image" in log_data:
                log_data["image"] = [log_data["image"][0][:80] + "... (truncated)"]
            print(f"Payload: {json.dumps(log_data)}")
            
            req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
            
        elif mode == "variation":
            url = f"{base_url}/images/variations"
            if not image_path:
                print("Error: --image path is required for variations mode.")
                sys.exit(1)
                
            fields = {
                "n": 1,
                "size": size,
                "model": chosen_model
            }
            if output_format:
                fields["output_format"] = output_format
            fields.update(extra_body)
            
            files = {
                "image": (os.path.basename(image_path), image_path)
            }
            req_body, mp_headers = encode_multipart_formdata(fields, files)
            headers.update(mp_headers)
            
            print(f"Calling: {url}")
            print(f"Image: {image_path}")
            
            req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
            
        elif mode == "edit":
            url = f"{base_url}/images/edits"
            if not image_path:
                print("Error: --image path is required for edit mode.")
                sys.exit(1)
                
            fields = {
                "prompt": prompt,
                "n": 1,
                "size": size,
                "model": chosen_model
            }
            if output_format:
                fields["output_format"] = output_format
            fields.update(extra_body)
            
            files = {
                "image": (os.path.basename(image_path), image_path)
            }
            if mask_path:
                files["mask"] = (os.path.basename(mask_path), mask_path)
                
            req_body, mp_headers = encode_multipart_formdata(fields, files)
            headers.update(mp_headers)
            
            print(f"Calling: {url}")
            print(f"Prompt: {prompt}")
            print(f"Image: {image_path}")
            if mask_path:
                print(f"Mask: {mask_path}")
                
            req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
            
        else:
            print(f"Error: Unknown mode '{mode}'")
            sys.exit(1)
            
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    
                    # OpenAI standard format: res_data['data'][0]['url'] or res_data['data'][0]['b64_json']
                    if "data" in res_data and len(res_data["data"]) > 0:
                        item = res_data["data"][0]
                        if "url" in item:
                            download_image(item["url"], output_path)
                        elif "b64_json" in item:
                            import base64
                            print("Decoding base64 image data...")
                            with open(output_path, "wb") as f:
                                f.write(base64.b64decode(item["b64_json"]))
                            print(f"Saved to {output_path}")
                        else:
                            print(f"Error: Unexpected response format item: {item}")
                            sys.exit(1)
                    else:
                        print(f"Error: Unexpected response format: {res_data}")
                        sys.exit(1)
                    
                    print(f"[AGENT GUIDANCE]\nSUCCESS. Saved image to {output_path}. Next: embed this image in your markdown file as `images/{output_path.name}` (or appropriate relative path).", file=sys.stderr)
                    # If execution reached here, it succeeded. Exit the retry loop.
                    break
                    
            except urllib.error.HTTPError as e:
                is_transient = e.code == 429 or (500 <= e.code < 600)
                if is_transient and attempt < max_attempts:
                    import time
                    import random
                    sleep_time = (2 ** attempt) + random.uniform(0.1, 1.0)
                    print(f"Transient HTTP Error {e.code} ({e.reason}) on attempt {attempt}/{max_attempts}. Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                
                print(f"HTTP Error: {e.code} - {e.reason}")
                try:
                    err_body = e.read().decode("utf-8")
                    print(f"Error body: {err_body}")
                except Exception:
                    pass
                print("[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
                      "The OpenAI-Compatible API returned a permanent error.\n"
                      "ACTION:\n"
                      "1. Verify that your API key, Base URL, and Model Name in .env are correct.\n"
                      "2. Verify you have sufficient quota and permission for the requested model.\n"
                      "3. FALLBACK: Fall back to the Agent Native engine (call generate_image tool) or the SVG Vector Diagram Engine.", file=sys.stderr)
                sys.exit(1)
                
            except urllib.error.URLError as e:
                if attempt < max_attempts:
                    import time
                    import random
                    sleep_time = (2 ** attempt) + random.uniform(0.1, 1.0)
                    print(f"Network URLError ({e.reason}) on attempt {attempt}/{max_attempts}. Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    continue
                
                print(f"URL Error: {e.reason}")
                print("[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
                      "Network connection failed after retries.\n"
                      "ACTION:\n"
                      "1. Check your internet connection or proxy settings.\n"
                      "2. Verify that the Base URL in .env is reachable.\n"
                      "3. FALLBACK: Fall back to the Agent Native engine (call generate_image tool) or the SVG Vector Diagram Engine.", file=sys.stderr)
                sys.exit(1)
                
            except Exception as e:
                print(f"Unexpected Error: {e}")
                print("[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
                      "An unexpected exception occurred.\n"
                      "FALLBACK: Fall back to the Agent Native engine (call generate_image tool) or the SVG Vector Diagram Engine.", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Request construction failed: {e}")
        print("[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
              "Request payload construction failed. Check input parameters (prompt, image path, extra body format).\n"
              "FALLBACK: Fall back to the Agent Native engine (call generate_image tool) or the SVG Vector Diagram Engine.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="OpenAI-compatible Image Generation & Editing Client")
    parser.add_argument("--mode", choices=["generate", "edit", "variation"], default="generate", help="API Operation Mode")
    parser.add_argument("--prompt", type=str, help="Text description for generation or edit")
    parser.add_argument("--image", type=str, help="Path to base image (required for edit/variation)")
    parser.add_argument("--mask", type=str, help="Path to mask image (optional for edit)")
    parser.add_argument("--size", type=str, default="1024x1024", help="Dimensions e.g. 1024x1024, 2K")
    parser.add_argument("--output", type=str, required=True, help="File path where output image will be saved")
    parser.add_argument("--model", type=str, help="Override default model name")
    parser.add_argument("--output-format", type=str, help="Image output format (e.g. png, jpeg)")
    parser.add_argument("--extra-body", type=str, help="Extra root-level body parameters as a JSON string")
    
    args = parser.parse_args()
    
    if args.mode in ["generate", "edit"] and not args.prompt:
        parser.error(f"--prompt is required when mode is '{args.mode}'")
        
    call_openai_compatible_api(
        mode=args.mode,
        prompt=args.prompt,
        image_path=args.image,
        mask_path=args.mask,
        size=args.size,
        output_path=args.output,
        model=args.model,
        output_format=args.output_format,
        extra_body_str=args.extra_body
    )

if __name__ == "__main__":
    main()
