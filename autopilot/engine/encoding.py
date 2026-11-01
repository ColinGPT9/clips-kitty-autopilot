"""Small portable adapter for the reused Gaming compositor."""


def video_encoder_args(config=None):
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-threads", "2"]


def audio_filter_args(normalize=True):
    return ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"] if normalize else []


def final_movflags():
    return ["-movflags", "+faststart"]
