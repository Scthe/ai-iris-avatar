def inject_path():
    """
    Called before anything else. You can use this function to e.g.
    add to the path additional source files. PyTorch with CUDA
    is 2.7+ GB, and you probably already have one installed.
    I don't want to waste your disk space.
    """
    import sys

    # your paths here
    # sys.path.append("C:/python312/lib/site-packages")  # PyTorch with CUDA (2.7+ GB)
    # sys.path.append("C:/programs/install/tts/env/Lib/site-packages")
    # sys.path.append("C:/programs/install/tts")
    # sys.path.append("C:/programs/install/stable-diffusion-webui/venv/Lib/site-packages")
    # sys.path.append('C:/programs/install/kohya_ss/venv/Lib/site-packages')
    pass
