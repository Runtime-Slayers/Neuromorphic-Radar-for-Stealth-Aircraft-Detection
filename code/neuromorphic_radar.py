"""
Neuromorphic Radar Signal Processing for Stealth Aircraft Detection
Bio-Inspired Visual Cortex Algorithms for Low-Observable Target Extraction
"""
import numpy as np

def simulate_radar_return(n_range=256, n_doppler=128, snr_db=-5, seed=42):
    np.random.seed(seed)
    noise_power = 1.0
    signal_power = noise_power * 10 ** (snr_db / 10)
    clutter = 0.5 * np.random.rayleigh(1.0, (n_range, n_doppler))
    noise   = np.random.randn(n_range, n_doppler) * np.sqrt(noise_power)
    cube = clutter + noise
    # Inject stealth target at low RCS
    t_r, t_d = n_range // 3, n_doppler // 2
    cube[t_r, t_d] += np.sqrt(signal_power) * 2
    return cube, (t_r, t_d)

def leaky_integrate_fire(input_map, threshold=1.5, leak=0.9):
    """LIF neuron layer — spike when membrane potential crosses threshold."""
    membrane = np.zeros_like(input_map)
    membrane = leak * membrane + input_map
    spikes = (membrane > threshold).astype(float)
    membrane[spikes > 0] = 0.0
    return spikes

def lateral_inhibition(spikes, radius=3):
    """Winner-take-all lateral inhibition across range-Doppler plane."""
    inhibited = spikes.copy()
    for r, d in zip(*np.where(spikes > 0)):
        r0, r1 = max(0, r - radius), min(spikes.shape[0], r + radius + 1)
        d0, d1 = max(0, d - radius), min(spikes.shape[1], d + radius + 1)
        patch = spikes[r0:r1, d0:d1]
        if spikes[r, d] < patch.max():
            inhibited[r, d] = 0
    return inhibited

def cfar_detector(cube, guard=2, train=8, pfa=1e-4):
    """Cell-Averaging CFAR detection."""
    detections = np.zeros_like(cube, dtype=bool)
    nr, nd = cube.shape
    total = (2 * (guard + train) + 1) ** 2 - (2 * guard + 1) ** 2
    for r in range(guard + train, nr - guard - train):
        for d in range(guard + train, nd - guard - train):
            window = cube[r-guard-train:r+guard+train+1, d-guard-train:d+guard+train+1].copy()
            guard_zone = cube[r-guard:r+guard+1, d-guard:d+guard+1]
            noise_est = (window.sum() - guard_zone.sum()) / total
            threshold = noise_est * (-np.log(pfa))
            detections[r, d] = cube[r, d] > threshold
    return detections

def neuromorphic_pipeline(cube):
    normed = (cube - cube.mean()) / (cube.std() + 1e-6)
    spikes = leaky_integrate_fire(normed)
    spikes = lateral_inhibition(spikes)
    return spikes

if __name__ == "__main__":
    print("Simulating radar range-Doppler cube (SNR = -5 dB)...")
    cube, target = simulate_radar_return()
    print(f"  Cube shape : {cube.shape}  Target at {target}")
    spikes = neuromorphic_pipeline(cube)
    print(f"  LIF spikes : {int(spikes.sum())}")
    cfar = cfar_detector(cube)
    detected = np.argwhere(cfar)
    near_target = [d for d in detected if abs(d[0]-target[0]) < 5 and abs(d[1]-target[1]) < 5]
    print(f"  CFAR detections: {len(detected)}  Near target: {len(near_target)}")
    print("Neuromorphic radar processing complete.")
