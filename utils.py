import json 
import re

def find_inner_segments(lookup_table, record, annotator, segstart, segend):
    # Initialize the list to hold the output (start, end, class)
    class_ranges = []
    
    # Iterate through the class ranges in the lookup table for the specific record
    for start, end, score in lookup_table[record][annotator]:
        # Check if the segment overlaps with the range (segstart, segend)
        if start <= segend and end >= segstart:
            # Calculate the overlap range
            overlap_start = max(start, segstart)
            overlap_end = min(end, segend)
            
            # Append the tuple of (start, end, class) for the overlapping range
            class_ranges.append((overlap_start, overlap_end, int(score)))
    return class_ranges

def load_json(path_to_file):
    with open(path_to_file, "r") as f:
        data = json.load(f)
    return data

def sample_to_time(sample_idx):
    '''
    Converts number or array of sample indices to a string or list of strings in the format hh:mm:ss.
    Uses hard-coded 1000Hz sampling rate.
    '''
    if hasattr(sample_idx, '__iter__'):
        out = [f"{int(v // 3600000):02}:{int((v % 3600000) // 60000):02}:{int((v % 60000) // 1000):02}" for v in sample_idx]
    else:
        out =  f"{int(sample_idx // 3600000):02}:{int((sample_idx % 3600000) // 60000):02}:{int((sample_idx % 60000) // 1000):02}"
    return out

def calc_c0_offset(lookup_table, record, annotator, sample_idx):
    '''
    NOTE: DOES NOT WORK YET
    Calculates the offset for class0 exclusion in overview plots.
    '''
    # sample_idx = sample_num - 1
    segments = lookup_table[record][annotator]
    offset = 0
    for (s, e, c) in segments:
        if c == 0:
            offset += e - s
        else:
            # if sample_idx is within a segment
            if (e - offset) >= sample_idx:
                print(e, offset, sample_idx)
                return offset
    return offset