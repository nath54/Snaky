# vulkan_protocols.py
from typing import Protocol

# Define a Protocol for VkImage (representing Vulkan image handle)
class VkImageProtocol(Protocol):
    """Protocol for VkImage type, representing a Vulkan image handle."""

    def bind_memory(self, memory: "VkDeviceMemoryProtocol") -> None:
        """Bind memory to the Vulkan image (simplified)."""
        pass

    def get_image_info(self) -> "VkImageCreateInfo":
        """Retrieve image creation info, which might be useful for certain operations."""
        pass


# Define a Protocol for VkInstance (representing Vulkan instance handle)
class VkInstanceProtocol(Protocol):
    """Protocol for VkInstance type, representing a Vulkan instance handle."""

    def destroy(self, allocator: "VkAllocationCallbacksProtocol") -> None:
        """Destroy the Vulkan instance."""
        pass


# Define a Protocol for VkDevice (representing Vulkan device handle)
class VkDeviceProtocol(Protocol):
    """Protocol for VkDevice type, representing a Vulkan device handle."""

    def create_command_pool(self, pool_info: "VkCommandPoolCreateInfo") -> "VkCommandPoolProtocol":
        """Create a Vulkan command pool (this will be a handle to a command pool)."""
        pass


# Define a Protocol for VkSwapchainKHR (representing Vulkan swapchain handle)
class VkSwapchainProtocol(Protocol):
    """Protocol for VkSwapchainKHR type, representing a Vulkan swapchain handle."""

    def get_swapchain_info(self) -> "VkSwapchainCreateInfoKHR":
        """Retrieve swapchain creation information."""
        pass


# Define a Protocol for VkDeviceMemory (representing Vulkan device memory handle)
class VkDeviceMemoryProtocol(Protocol):
    """Protocol for VkDeviceMemory type, representing Vulkan device memory handle."""

    def allocate(self, size: int, memory_type: int) -> None:
        """Allocate Vulkan memory."""
        pass


# Define a Protocol for VkImageCreateInfo (representing Vulkan image creation info)
class VkImageCreateInfo(Protocol):
    """Protocol for VkImageCreateInfo, representing image creation parameters in Vulkan."""

    def __init__(self, *args, **kwargs) -> None:
        pass  # This would hold the parameters for image creation


# Define a Protocol for VkAllocationCallbacks (representing allocation callbacks in Vulkan)
class VkAllocationCallbacksProtocol(Protocol):
    """Protocol for VkAllocationCallbacks, used in various Vulkan object creation and destruction operations."""

    def set_allocation_function(self, allocate: callable) -> None:
        """Set a custom allocation function."""
        pass

    def set_free_function(self, free: callable) -> None:
        """Set a custom free function."""
        pass


# Define a Protocol for VkCommandPoolCreateInfo (representing command pool creation info)
class VkCommandPoolCreateInfo(Protocol):
    """Protocol for VkCommandPoolCreateInfo, representing parameters for command pool creation."""

    def __init__(self, *args, **kwargs) -> None:
        pass  # This would hold the parameters for command pool creation


# Define a Protocol for VkCommandPool (representing Vulkan command pool handle)
class VkCommandPoolProtocol(Protocol):
    """Protocol for VkCommandPool, representing a command pool in Vulkan."""

    def reset(self) -> None:
        """Reset the command pool."""
        pass


# Define a Protocol for VkSwapchainCreateInfoKHR (representing swapchain creation info in Vulkan)
class VkSwapchainCreateInfoKHR(Protocol):
    """Protocol for VkSwapchainCreateInfoKHR, representing parameters for swapchain creation."""

    def __init__(self, *args, **kwargs) -> None:
        pass  # This would hold the parameters for swapchain creation
