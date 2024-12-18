
from typing import Optional

import vulkan as vk  # type: ignore

# Initialize Vulkan
def init_vulkan() -> Optional[object]:
    # Application Info
    app_info: vk.VkApplicationInfo = vk.VkApplicationInfo(
        sType=vk.VK_STRUCTURE_TYPE_APPLICATION_INFO,
        pApplicationName='SDL2-Vulkan Example',
        applicationVersion=vk.VK_MAKE_VERSION(1, 0, 0),
        pEngineName='No Engine',
        engineVersion=vk.VK_MAKE_VERSION(1, 0, 0),
        apiVersion=vk.VK_API_VERSION_1_0
    )

    # Instance Create Info
    create_info: vk.VkInstanceCreateInfo = vk.VkInstanceCreateInfo(
        sType=vk.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        pNext=None,
        flags=0,
        pApplicationInfo=app_info,
        enabledLayerCount=0,
        ppEnabledLayerNames=None,
        enabledExtensionCount=0,
        ppEnabledExtensionNames=None
    )

    # Create the Vulkan instance
    try:
        instance: object = vk.vkCreateInstance(create_info, None)
        return instance
    except vk.VkError as e:
        print(f"Failed to create Vulkan instance: {e}")
        return None


