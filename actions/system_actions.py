import ctypes


# Windows virtual key codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_KEYUP = 0x0002


def press_media_key(key_code):
    """
    Simulate pressing a Windows media key.
    """

    try:
        ctypes.windll.user32.keybd_event(
            key_code,
            0,
            0,
            0
        )

        ctypes.windll.user32.keybd_event(
            key_code,
            0,
            KEYEVENTF_KEYUP,
            0
        )

        return True

    except Exception as error:
        print(f"Media key error: {error}")
        return False


def volume_up():
    """
    Increase Windows system volume.
    """

    if press_media_key(VK_VOLUME_UP):
        return "Turning the volume up."

    return "I couldn't increase the volume."


def volume_down():
    """
    Decrease Windows system volume.
    """

    if press_media_key(VK_VOLUME_DOWN):
        return "Turning the volume down."

    return "I couldn't decrease the volume."


def mute_volume():
    """
    Toggle Windows system mute.
    """

    if press_media_key(VK_VOLUME_MUTE):
        return "Toggling mute."

    return "I couldn't change the mute setting."