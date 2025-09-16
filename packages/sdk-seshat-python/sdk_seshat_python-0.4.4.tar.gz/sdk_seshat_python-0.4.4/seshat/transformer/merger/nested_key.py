from typing import Optional, List, Union

from seshat.data_class import SFrame, GroupSFrame, DFrame, SPFrame
from seshat.transformer.merger.base import SFrameMerger


class NestedKeyMerger(SFrameMerger):
    """
    A merger that searches for a specific key in a nested GroupSFrame structure
    and merges the frames found with this key using the built-in extend functionality.

    This merger supports both pandas (DFrame) and PySpark (SPFrame) DataFrames and is designed
    to work with the output of a Branch transformer where:
    - The input is a GroupSFrame
    - The children of the input are also GroupSFrames
    - The children of the children are dictionaries mapping strings to frames

    Parameters
    ----------
    group_key : str
        The key to search for in the nested structure
    result_key : str, optional
        The key to use for the result in the output GroupSFrame.
        If not provided, the group_key will be used.

    Examples
    --------
    >>> branch = Branch(pipe_map=pipe_map)
    >>> result = branch(sf_input)  # result is a GroupSFrame with GroupSFrame children
    >>> merger = NestedKeyMerger(group_key="user_data")
    >>> merged_result = merger(result)  # merged_result is a GroupSFrame with a single frame
    """

    def __init__(
        self, group_key: str, result_key: Optional[str] = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.group_key = group_key
        self.result_key = result_key or group_key

    def _find_nested_frames(
        self, sf_input: GroupSFrame
    ) -> List[Union[DFrame, SPFrame]]:
        frames = []

        for child_key, child_sf in sf_input.children.items():
            # Look for the group_key in the children of the child
            frames.append(child_sf.get(self.group_key))

        return frames

    def __call__(self, sf_input: SFrame, *args, **kwargs) -> SFrame:
        if not isinstance(sf_input, GroupSFrame):
            return sf_input

        # Find all frames with the group_key
        frames = self._find_nested_frames(sf_input)

        if not frames:
            return sf_input

        # Merge frames
        result_frame = frames[0].__copy__()

        # Extend with the rest using the built-in extend method
        for frame in frames[1:]:
            result_frame.extend(frame.data)

        if result_frame is None:
            return sf_input

        # Create a new GroupSFrame with the result
        result = GroupSFrame()
        result[self.result_key] = result_frame

        return result

    def calculate_complexity(self):
        return 15
