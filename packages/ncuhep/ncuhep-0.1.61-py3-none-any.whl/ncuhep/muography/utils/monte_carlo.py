import numpy as np
import matplotlib.pyplot as plt
from numba import njit, prange
from coordinates import det2earth, earth2det, cart2slope
from tracking import track_reconstruction
from flux import effective_area, solid_angle
import time


@njit
def homogenous_generator(theta_max_deg: float, zenith_boresight_deg: float, azimuth_boresight_deg: float, half_length_x: float, half_length_y: float):
    theta_max_rad = np.radians(theta_max_deg)
    cos_theta = np.random.uniform(np.cos(theta_max_rad), 1)
    theta = np.arccos(cos_theta)
    phi = np.random.uniform(0, 2 * np.pi)

    x_dir_det = np.sin(theta) * np.cos(phi)
    y_dir_det = np.sin(theta) * np.sin(phi)
    z_dir_det = np.cos(theta)

    x_pos_det = 0
    y_pos_det = 0
    z_pos_det = 0

    x_pp = np.random.uniform(-half_length_x, half_length_x)
    y_pp = np.random.uniform(-half_length_y, half_length_y)
    z_pp = 0

    x_pos_det += -x_pp * np.sin(phi) - y_pp * np.cos(theta) * np.cos(phi) + z_pp * np.sin(theta) * np.cos(phi)
    y_pos_det += x_pp * np.cos(phi) - y_pp * np.cos(theta) * np.sin(phi) + z_pp * np.sin(theta) * np.sin(phi)
    z_pos_det += y_pp * np.sin(theta) + z_pp * np.cos(theta)

    x_dir_earth, y_dir_earth, z_dir_earth = det2earth(x_dir_det, y_dir_det, z_dir_det, zenith_boresight_deg, azimuth_boresight_deg)
    x_pos_earth, y_pos_earth, z_pos_earth = det2earth(x_pos_det, y_pos_det, z_pos_det, zenith_boresight_deg, azimuth_boresight_deg)

    return np.array([x_pos_earth, y_pos_earth, z_pos_earth]), np.array([x_dir_earth, y_dir_earth, z_dir_earth])


@njit
def detection_simulation(layer_z: np.ndarray, pixel_length_x: float, pixel_length_y: float, layer_half_length_x: np.ndarray, layer_half_length_y: np.ndarray, zenith_boresight_deg: float, azimuth_boresight_deg: float, particle_pos_earth: np.ndarray, particle_dir_earth: np.ndarray, mode: int):

    particle_dir_det = earth2det(particle_dir_earth[0], particle_dir_earth[1], particle_dir_earth[2], zenith_boresight_deg, azimuth_boresight_deg)
    particle_pos_det = earth2det(particle_pos_earth[0], particle_pos_earth[1], particle_pos_earth[2], zenith_boresight_deg, azimuth_boresight_deg)

    theta_x = np.arctan2(particle_dir_det[0], particle_dir_det[2])
    theta_y = np.arctan2(particle_dir_det[1], particle_dir_det[2])

    x = np.tan(theta_x) * (layer_z - particle_pos_det[2]) + particle_pos_det[0]
    y = np.tan(theta_y) * (layer_z - particle_pos_det[2]) + particle_pos_det[1]

    if mode == 0:
        x = np.round(x / pixel_length_x) * pixel_length_x
        y = np.round(y / pixel_length_y) * pixel_length_y
    elif mode == 1:
        x = np.floor(x / pixel_length_x) * pixel_length_x + pixel_length_x / 2
        y = np.floor(y / pixel_length_y) * pixel_length_y + pixel_length_y / 2
    else:
        raise ValueError("mode must be 0 or 1")

    hits = np.zeros((len(layer_z), 3), dtype=np.float32)
    hit = True
    for i in range(len(layer_z)):
        if np.abs(x[i]) <= layer_half_length_x[i] and np.abs(y[i]) <= layer_half_length_y[i]:
            hits[i, 0] = x[i]
            hits[i, 1] = y[i]
            hits[i, 2] = layer_z[i]
        else:
            hits[i, 0] = np.nan
            hits[i, 1] = np.nan
            hits[i, 2] = layer_z[i]
            hit = False

    return hits, hit


@njit(parallel=True)
def run_homogenous_simulation(num_particles: int, theta_max_deg: float, zenith_boresight_deg: float, azimuth_boresight_deg: float, half_length_x: float, half_length_y: float, layer_z: np.ndarray, pixel_length_x: float, pixel_length_y: float, layer_half_length_x: np.ndarray, layer_half_length_y: np.ndarray, mask=None):
    all_hit = np.zeros(num_particles, dtype=np.bool_)
    all_measured = np.empty((num_particles, 4), dtype=np.float32)
    all_simulated = np.empty((num_particles, 3), dtype=np.float32)
    for i in prange(num_particles):
        particle_pos_earth, particle_dir_earth = homogenous_generator(theta_max_deg, zenith_boresight_deg, azimuth_boresight_deg, half_length_x, half_length_y)
        hits, hit = detection_simulation(layer_z, pixel_length_x, pixel_length_y, layer_half_length_x, layer_half_length_y, zenith_boresight_deg, azimuth_boresight_deg, particle_pos_earth, particle_dir_earth, mode=1)
        if mask is not None:
            hits = hits[mask]
        all_hit[i] = hit
        all_measured[i] = track_reconstruction(hits) if hit else np.array([np.nan, np.nan, np.nan, np.nan], dtype=np.float32)
        r, theta_x, theta_y = cart2slope(particle_dir_earth[0], particle_dir_earth[1], particle_dir_earth[2])
        all_simulated[i] = np.array([r, np.degrees(theta_x), np.degrees(theta_y)], dtype=np.float32)

    return all_simulated[all_hit], all_measured[all_hit]


@njit(parallel=True)
def compute_basis(simulated_hits: np.ndarray, detected_hits: np.ndarray, opening_angle_deg=25, basis=None):
    detected_hits = np.round(detected_hits, decimals=1)
    theta_x_unique = np.unique(detected_hits[:, 2])
    theta_y_unique = np.unique(detected_hits[:, 3])

    angle = opening_angle_deg
    mrad = int(np.radians(angle) * 1000)
    nx = np.arange(- mrad, mrad + 1)
    ny = np.arange(- mrad, mrad + 1)

    cx = np.amin(nx)
    cy = np.amin(ny)

    simulated = simulated_hits[:, 1:3]
    detected = detected_hits[:, 2:4]

    if basis is None:
        basis = np.zeros((len(theta_x_unique), len(theta_y_unique), len(nx), len(ny)), dtype=np.int32)

    for i in prange(simulated.shape[0]):
        dx = np.zeros(8, dtype=np.float32)
        dy = np.zeros(8, dtype=np.float32)

        ix = np.zeros(8, dtype=np.int32)
        iy = np.zeros(8, dtype=np.int32)

        sx = np.zeros(8, dtype=np.float32)
        sy = np.zeros(8, dtype=np.float32)

        dx_ = detected[i, 0]
        dy_ = detected[i, 1]

        dx[0], dy[0] = dx_, dy_
        dx[1], dy[1] = -dx_, dy_
        dx[2], dy[2] = dx_, -dy_
        dx[3], dy[3] = -dx_, -dy_
        dx[4], dy[4] = dy_, dx_
        dx[5], dy[5] = -dy_, dx_
        dx[6], dy[6] = dy_, -dx_
        dx[7], dy[7] = -dy_, -dx_

        for j in range(8):
            ix[j] = np.searchsorted(theta_x_unique, dx[j])
            iy[j] = np.searchsorted(theta_y_unique, dy[j])

        x_ = np.round(np.radians(simulated[i, 0]) * 1000)
        y_ = np.round(np.radians(simulated[i, 1]) * 1000)

        sx[0], sy[0] = x_, y_
        sx[1], sy[1] = -x_, y_
        sx[2], sy[2] = x_, -y_
        sx[3], sy[3] = -x_, -y_
        sx[4], sy[4] = y_, x_
        sx[5], sy[5] = -y_, x_
        sx[6], sy[6] = y_, -x_
        sx[7], sy[7] = -y_, -x_

        sx -= cx
        sy -= cy

        for j in range(8):
            basis[ix[j], iy[j], int(sx[j]), int(sy[j])] += 1


    return basis, theta_x_unique, theta_y_unique, nx, ny


if __name__ == "__main__":
    layer_z = np.array([-750, -250, 250, 750], dtype=np.float32)
    pixel_length_x = 50
    pixel_length_y = 50
    layer_half_length_x = np.array([300, 200, 200, 300], dtype=np.float32)
    layer_half_length_y = np.array([300, 200, 200, 300], dtype=np.float32)
    zenith_boresight_deg = 0.0
    azimuth_boresight_deg = 0.0
    theta_max_deg = 30.0
    half_length_x = 300
    half_length_y = 300

    flux = 1
    solid_angle_ = 2 * np.pi * (1 - np.cos(np.radians(theta_max_deg)))
    area = (2 * half_length_x / 1000) * (2 * half_length_y / 1000)
    exposure_time = 3650 * 24 * 3600  # 3650 days in seconds
    mask = np.array([True, False, True, True])
    geometric_factor = solid_angle_ * area

    num_particles = int(flux * solid_angle_ * area * exposure_time)

    angle = 25
    mrad = int(np.radians(angle) * 1000)
    theta_x_mrad = np.arange(-mrad, mrad + 1)
    theta_y_mrad = np.arange(-mrad, mrad + 1)

    theta_x_rad, theta_y_rad = np.meshgrid(theta_x_mrad / 1000, theta_y_mrad / 1000)

    area = np.zeros(theta_x_rad.shape, dtype=np.float32)
    sa = np.zeros(theta_x_rad.shape, dtype=np.float32)
    for i in range(theta_x_rad.shape[0]):
        for j in range(theta_x_rad.shape[1]):
            area[i, j] = effective_area(theta_x_rad[i, j], theta_y_rad[i, j], layer_z, layer_half_length_x, layer_half_length_y) / 1000 / 1000
            sa[i, j] = solid_angle(theta_x_rad[i, j], theta_y_rad[i, j], 1 / 1000, 1 / 1000)

    geometric_factor_array = area * sa


    runs = 1
    while True:
        print(f"Run {runs}")
        total_counts = 0
        target_counts = 100_000_000
        simulated_hits, detected_hits = run_homogenous_simulation(num_particles, theta_max_deg, zenith_boresight_deg, azimuth_boresight_deg, half_length_x, half_length_y, layer_z, pixel_length_x, pixel_length_y, layer_half_length_x, layer_half_length_y, mask=mask)
        basis, theta_x_unique, theta_y_unique, nx, ny = compute_basis(simulated_hits, detected_hits)

        total_counts += simulated_hits.shape[0]
        total_time = 0
        i = 0
        while True:
            start_time = time.time()
            simulated_hits, detected_hits = run_homogenous_simulation(num_particles, theta_max_deg, zenith_boresight_deg, azimuth_boresight_deg, half_length_x, half_length_y, layer_z, pixel_length_x, pixel_length_y, layer_half_length_x, layer_half_length_y, mask=mask)
            basis, theta_x_unique, theta_y_unique, nx, ny = compute_basis(simulated_hits, detected_hits, basis=basis)
            total_counts += simulated_hits.shape[0]
            end_time = time.time()
            total_time += end_time - start_time
            print(f"Iteration {i+1}: Processed {simulated_hits.shape[0]} hits in {end_time - start_time:.2f} seconds. Total counts: {total_counts}. Total time: {total_time:.2f} seconds. Average time per iteration: {total_time / (i + 1):.2f} seconds.")
            i += 1
            if total_counts >= target_counts:
                break

        # if exists, load and add
        try:
            old_basis = np.load("monte_carlo_basis_2.npy")
            basis += old_basis
            print("Loaded existing basis and added to current basis.")
        except FileNotFoundError:
            print("No existing basis found. Saving current basis.")

        np.save("monte_carlo_basis_2.npy", basis)

        image = np.sum(basis, axis=(0, 1))

        particle_counts = np.sum(basis)
        image = image.astype(np.float64)
        image[geometric_factor_array > 0] /= geometric_factor_array[geometric_factor_array > 0]

        mean = np.mean(image[image > 0])
        std = np.std(image[image > 0])

        with open("monte_carlo_info_2.txt", "a") as f:
            string_ = f"{std/mean*100}, {particle_counts}\n"
            f.write(string_)

        print(f"{std/mean * 100:.2f}% uncertainty with {particle_counts:.2E} particles")

        measured_angles_x, measured_angles_y = np.meshgrid(theta_x_unique, theta_y_unique)
        measured_angles = np.array([measured_angles_x, measured_angles_y])
        measured_angles = np.radians(measured_angles) * 1000

        incident_angles_x, incident_angles_y = np.meshgrid(nx, ny)
        incident_angles = np.array([incident_angles_x, incident_angles_y])

        dictionary = {
            "basis": basis,
            "measured_angles": measured_angles,
            "incident_angles": incident_angles,
            "geometric_factor": geometric_factor_array
        }

        np.savez_compressed("9449_2.npz", **dictionary)
        print("Saved 9449_2.npz")

        runs += 1

        if np.amax(basis) >= 2_000_000_000:
            break
    # simulated_hits, detected_hits = run_simulation(num_particles)
    # np.save("../../simulation_1flux_36500days2.npy", detected_hits)

