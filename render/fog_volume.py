"""第 51 批：体积雾一进洞穴就整片发灰：froxel 深度按近..."""

def slice_depth(index, slices, z_near, z_far):
    """返回第 index 个 froxel 切片的深度，按指数分布。"""
    raise NotImplementedError("TODO: slice_depth")

def spot_weight(cos_angle, cos_outer, cos_inner):
    """返回聚光锥权重，外锥为 0、内锥为 1。"""
    raise NotImplementedError("TODO: spot_weight")

def upsample_weight(depth_center, depth_neighbor):
    """返回邻域像素在升采样中的归一化权重。"""
    raise NotImplementedError("TODO: upsample_weight")

def history_is_valid(prev_depth, curr_depth, tol=0.05):
    """判断时域历史是否可复用。"""
    raise NotImplementedError("TODO: history_is_valid")

def triplanar_weight(nx, ny, nz):
    """返回三平面映射的三个归一化权重。"""
    raise NotImplementedError("TODO: triplanar_weight")

def density_in_box(point, box_min, box_max):
    """判断点是否落在体积雾盒内。"""
    raise NotImplementedError("TODO: density_in_box")
