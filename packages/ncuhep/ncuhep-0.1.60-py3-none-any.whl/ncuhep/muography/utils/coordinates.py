import numpy as np
from numba import njit


@njit
def cart2slope(x: float, y: float, z: float):
    r = np.sqrt(x**2 + y**2 + z**2)
    theta_x = np.arctan2(x, z)
    theta_y = np.arctan2(y, z)

    return r, theta_x, theta_y


@njit
def cart2slope_vec(p: np.ndarray):
    # Reshape to (-1, 3) to handle arbitrary dimensions
    original_shape = p.shape[:-1]
    x_reshaped = p.reshape(-1, 3)

    x0 = x_reshaped[:, 0]
    x1 = x_reshaped[:, 1]
    x2 = x_reshaped[:, 2]

    r = np.sqrt(x0 ** 2 + x1 ** 2 + x2 ** 2)
    theta_x = np.degrees(np.arctan2(x0, x2))
    theta_y = np.degrees(np.arctan2(x1, x2))

    v = np.empty((x_reshaped.shape[0], 3))
    v[:, 0] = r
    v[:, 1] = theta_x
    v[:, 2] = theta_y

    # Reshape back to the original dimensions
    return v.reshape(*original_shape, 3)


@njit
def slope2cart(r: float, theta_x_deg: float, theta_y_deg: float):
    theta_x = np.radians(theta_x_deg)
    theta_y = np.radians(theta_y_deg)

    x = r * np.tan(theta_x) / np.sqrt(1 + np.tan(theta_x) ** 2 + np.tan(theta_y) ** 2)
    y = r * np.tan(theta_y) / np.sqrt(1 + np.tan(theta_x) ** 2 + np.tan(theta_y) ** 2)
    z = r / np.sqrt(1 + np.tan(theta_x) ** 2 + np.tan(theta_y) ** 2)

    return x, y, z


@njit
def slope2cart_vec(p: np.ndarray):
    # Reshape to (-1, 3) to handle arbitrary dimensions
    original_shape = p.shape[:-1]
    p_reshaped = p.reshape(-1, 3)

    r = p_reshaped[:, 0]
    theta_x = p_reshaped[:, 1]
    theta_y = p_reshaped[:, 2]

    x = r * np.tan(theta_x) / np.sqrt(1 + np.tan(theta_x) ** 2 + np.tan(theta_y) ** 2)
    y = r * np.tan(theta_y) / np.sqrt(1 + np.tan(theta_x) ** 2 + np.tan(theta_y) ** 2)
    z = r / np.sqrt(1 + np.tan(theta_x) ** 2 + np.tan(theta_y) ** 2)

    cartesian = np.empty((p_reshaped.shape[0], 3))
    cartesian[:, 0] = x
    cartesian[:, 1] = y
    cartesian[:, 2] = z

    # Reshape back to the original dimensions
    return cartesian.reshape(*original_shape, 3)


@njit
def rotational_matrix(zenith_det_deg: float, azimuth_det_deg: float):
    zenith = np.radians(zenith_det_deg)
    azimuth = -np.radians(azimuth_det_deg)

    R = np.array([
        [np.cos(azimuth), -np.sin(azimuth), 0],
        [np.sin(azimuth) * np.cos(zenith), np.cos(azimuth) * np.cos(zenith), -np.sin(zenith)],
        [np.sin(azimuth) * np.sin(zenith), np.sin(zenith) * np.cos(azimuth), np.cos(zenith)]
    ])

    return R


@njit
def earth2det(x: float, y: float, z: float, zenith_det_deg: float, azimuth_det_deg: float):
    X = np.array([x, y, z])
    R = rotational_matrix(zenith_det_deg, azimuth_det_deg)

    Xp = R @ X
    xp, yp, zp = Xp[0], Xp[1], Xp[2]

    return xp, yp, zp


@njit
def earth2det_vec(p: np.ndarray, zenith_det_deg: float, azimuth_det_deg: float):
    # Reshape to (-1, 3) to handle arbitrary dimensions
    original_shape = p.shape[:-1]
    p_reshaped = p.reshape(-1, 3)

    R = rotational_matrix(zenith_det_deg, azimuth_det_deg)

    Xp = R @ p_reshaped.T
    xp = Xp[0, :]
    yp = Xp[1, :]
    zp = Xp[2, :]

    dct = np.empty((p_reshaped.shape[0], 3))
    dct[:, 0] = xp
    dct[:, 1] = yp
    dct[:, 2] = zp

    # Reshape back to the original dimensions
    return dct.reshape(*original_shape, 3)


@njit
def det2earth(xp: float, yp: float, zp: float, zenith_det_deg: float, azimuth_det_deg: float):
    Xp = np.array([xp, yp, zp])
    R = rotational_matrix(zenith_det_deg, azimuth_det_deg)
    Rt = R.T

    X = Rt @ Xp
    x, y, z = X[0], X[1], X[2]

    return x, y, z


@njit
def det2earth_vec(p: np.ndarray, zenith_det_deg: float, azimuth_det_deg: float):
    # Reshape to (-1, 3) to handle arbitrary dimensions
    original_shape = p.shape[:-1]
    p_reshaped = p.reshape(-1, 3)

    R = rotational_matrix(zenith_det_deg, azimuth_det_deg)
    Rt = R.T

    X = Rt @ p_reshaped.T
    x = X[0, :]
    y = X[1, :]
    z = X[2, :]

    earth = np.empty((p_reshaped.shape[0], 3))
    earth[:, 0] = x
    earth[:, 1] = y
    earth[:, 2] = z

    # Reshape back to the original dimensions
    return earth.reshape(*original_shape, 3)


@njit
def zenith_azimuth_deg(theta_x: float, theta_y: float, zenith_det_deg: float, azimuth_det_deg: float):
    zenith = np.radians(zenith_det_deg)

    xp, yp, zp = slope2cart(1.0, theta_x, theta_y)

    x, y, z = det2earth(xp, yp, zp, zenith_det_deg, azimuth_det_deg)

    cos_zenith = -np.sin(zenith) * yp + np.cos(zenith) * zp
    zenith_deg = np.degrees(np.arccos(cos_zenith))

    azimuth_deg = np.degrees(np.arctan2(-x, y))

    if azimuth_deg < 0:
        azimuth_deg += 360.0

    return zenith_deg, azimuth_deg


@njit
def zenith_azimuth_deg_vec(p: np.ndarray, zenith_det_deg: float, azimuth_det_deg: float):
    # Reshape to (-1, 2) to handle arbitrary dimensions
    original_shape = p.shape[:-1]
    p_reshaped = p.reshape(-1, 2)

    zenith = np.radians(zenith_det_deg)

    theta_x = p_reshaped[:, 0]
    theta_y = p_reshaped[:, 1]

    xp, yp, zp = slope2cart_vec(np.column_stack((np.ones(theta_x.shape), theta_x, theta_y))).T

    x, y, z = det2earth_vec(np.column_stack((xp, yp, zp)), zenith_det_deg, azimuth_det_deg).T

    cos_zenith = -np.sin(zenith) * yp + np.cos(zenith) * zp
    zenith_deg = np.degrees(np.arccos(cos_zenith))

    azimuth_deg = np.degrees(np.arctan2(-x, y))

    for i in range(azimuth_deg.shape[0]):
        if azimuth_deg[i] < 0:
            azimuth_deg[i] += 360.0

    za = np.empty((p_reshaped.shape[0], 2))
    za[:, 0] = zenith_deg
    za[:, 1] = azimuth_deg

    # Reshape back to the original dimensions
    return za.reshape(*original_shape, 2)


if __name__ == "__main__":
    theta_x = 0
    theta_y = 0

    xp, yp, zp = slope2cart(1.0, theta_x, theta_y)

    print(f"xp: {xp}, yp: {yp}, zp: {zp}")

    zenith_det_deg = 10
    azimuth_det_deg = 0

    zenith_deg, azimuth_deg = zenith_azimuth_deg(theta_x, theta_y, zenith_det_deg, azimuth_det_deg)

    print(f"zenith_deg: {zenith_deg}, azimuth_deg: {azimuth_deg}")