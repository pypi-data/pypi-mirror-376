import numpy as np
from numba import njit
from tqdm import tqdm
import os


@njit
def pcnt_correction(pcnt):
    timestamp = np.zeros_like(pcnt)
    previous_timestamp = None

    for n, pcnt in enumerate(pcnt):
        if previous_timestamp is None:
            previous_timestamp = pcnt
            timestamp[n] = pcnt
        else:
            if pcnt < previous_timestamp:
                if previous_timestamp - pcnt > 2**17:
                    timestamp[n] = pcnt + 2**20
                else:
                    timestamp[n] = previous_timestamp
            else:
                timestamp[n] = pcnt

            previous_timestamp = timestamp[n]

    return timestamp


def get_timestamp(pcnt, tcnt):
    pcnt = pcnt.astype(np.uint64)
    pcnt = pcnt << 32
    tcnt = tcnt.astype(np.uint64)

    timestamp = pcnt + tcnt
    return timestamp


def get_layer(boardID, mapping):
    layerID = np.zeros(len(boardID))
    for N in range(len(boardID)):
        ID = boardID[N]
        layerID[N] = mapping[int(ID)-1]

    return layerID


def get_unique_id(boardID, channelID, mapping):

    unique_id = np.zeros_like(boardID, dtype=np.uint16)
    for n in range(len(boardID)):
        unique_id[n] = mapping[int(boardID[n]-1), int(channelID[n])]

    return unique_id


# 0 - Type
# 1 - Board ID
# 2 - Channel ID
# 3 - EVT
# 4 - Timestamp
# 5 - PCNT
# 6 - TCNT
# 7 - PWIDTH


@njit
def label(timestamp, event_threshold=75, hit_threshold=15):
    current_label = 0
    initial_timestamp = timestamp[0]
    previous_timestamp = timestamp[0]
    labels = np.zeros(len(timestamp), dtype=np.uint64)


    for n in range(1, len(timestamp)):
        current_timestamp = timestamp[n]

        if current_timestamp - previous_timestamp > hit_threshold or current_timestamp - initial_timestamp > event_threshold:
            current_label += 1
            initial_timestamp = current_timestamp

        previous_timestamp = current_timestamp
        labels[n] = current_label

    return labels


def event_selection(event):
    layer_ids = event["LAYERID"]
    layer_id, counts = np.unique(layer_ids, return_counts=True)

    if len(layer_id) < 4:
        return False
    elif counts[0] > 3 or counts[1] > 3 or counts[2] > 3 or counts[3] > 2 or len(layer_ids) > 8:
        return False
    else:
        return True



def event_grouping(data, event_selection):
    # Create a structured array for all hits
    dtype = [
        ("EVENTID", data["EVENTID"].dtype),
        ("BOARDID", data["BOARDID"].dtype),
        ("CHANNELID", data["CHANNELID"].dtype),
        ("LAYERID", data["LAYERID"].dtype),
        ("UNIQUEID", data["UNIQUEID"].dtype),
        ("TIMESTAMP", data["TIMESTAMP"].dtype),
        ("PCNT", data["PCNT"].dtype),
        ("TCNT", data["TCNT"].dtype),
        ("PWIDTH", data["PWIDTH"].dtype),
    ]
    hits = np.empty(len(data["EVENTID"]), dtype=dtype)
    for key in hits.dtype.names:
        hits[key] = data[key]

    # Group by EVENTID and filter events
    event_ids, start_idx, counts = np.unique(hits["EVENTID"], return_index=True, return_counts=True)
    keep_mask = np.zeros(len(hits), dtype=bool)

    for eid, idx, count in zip(event_ids, start_idx, counts):
        event_slice = slice(idx, idx + count)
        event = {k: hits[k][event_slice] for k in hits.dtype.names if k != "EVENTID"}
        if event_selection(event):
            keep_mask[event_slice] = True

    return hits[keep_mask]


def parser(dir, file, unique_id_mapping, layer_mapping, event_selection, event_threshold=75, hit_threshold=75):
    filepath = os.path.join(dir, file)

    # First pass: count valid lines (skip those with "Frame")
    valid_line_count = 0
    total_line_count = 0
    with open(filepath, "r") as f:
        for line in f:
            if not line.startswith("#Frame"):
                valid_line_count += 1
            total_line_count += 1


    # Preallocate arrays with the exact number of rows needed
    BOARDID   = np.empty(valid_line_count, dtype=np.uint8)
    CHANNELID = np.empty(valid_line_count, dtype=np.uint8)
    TIMESTAMP = np.empty(valid_line_count, dtype=np.float64)
    PCNT      = np.empty(valid_line_count, dtype=np.uint32)
    TCNT      = np.empty(valid_line_count, dtype=np.uint32)
    PWIDTH    = np.empty(valid_line_count, dtype=np.uint8)

    # Second pass: fill the preallocated arrays
    idx = 0
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("#Frame"):
                continue
            values = line.split("\t")
            # Convert values as needed and store them directly.
            BOARDID[idx]   = int(values[1])
            CHANNELID[idx] = int(values[2])
            TIMESTAMP[idx] = float(values[4])
            PCNT[idx]      = int(values[5])
            TCNT[idx]      = int(values[6])
            PWIDTH[idx]    = int(values[7])
            idx += 1

            # if idx >= valid_line_count:
            #     break

    data = {
        "BOARDID": BOARDID,
        "CHANNELID": CHANNELID,
        "TIMESTAMP": TIMESTAMP,
        "PCNT": PCNT,
        "TCNT": TCNT,
        "PWIDTH": PWIDTH
    }

    # mask = data["PWIDTH"] > 15
    # data = {key: data[key][mask] for key in data}

    data["PCNT"] = pcnt_correction(data["PCNT"])

    timeelapsed = np.amax(data["PCNT"]) - np.amin(data["PCNT"])

    if timeelapsed > 87000:
        print(f"Time elapsed: {timeelapsed}")

    data["TIMESTAMP"] = get_timestamp(data["PCNT"], data["TCNT"]).astype(np.uint64)

    sort = np.argsort(data["TIMESTAMP"])

    data = {key: data[key][sort] for key in data}


    data["UNIQUEID"] = get_unique_id(data["BOARDID"], data["CHANNELID"], unique_id_mapping)
    data["LAYERID"] = get_layer(data["BOARDID"], layer_mapping)
    data["EVENTID"] = label(data["TIMESTAMP"], event_threshold=event_threshold, hit_threshold=hit_threshold)

    events = event_grouping(data, event_selection)

    np.savez_compressed(f"{dir}/{file.split('.')[0]}.npz", events)

    del data


if __name__ == "__main__":
    filenames = ["/data9/MuographyPython/Data/Simulation/Geant4/modified_gaisser_9449/0"]
    unique_id_mapping = np.loadtxt("forward.txt", dtype=np.int64).reshape(26, 16)
    layer_mapping = np.loadtxt("layer.txt", dtype=np.int64)

    for filename in filenames:
        files = [f for f in os.listdir(filename) if f.endswith(".txt")]

        files = sorted(files)

        for file in tqdm(files):
            print(f"Processing {file}")
            parser(filename, file)

        # # Uncomment the following lines to use multiprocessing
        # with ProcessPoolExecutor() as executor:
        #     list(tqdm(executor.map(worker, [filename]*len(files), files), total=len(files)))

        print("Done")