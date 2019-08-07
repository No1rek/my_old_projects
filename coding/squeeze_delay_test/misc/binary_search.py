def binarySearch(data, val):
    lo, hi = 0, len(data) - 1
    best_ind = lo
    while lo <= hi:
        mid = int(lo + (hi - lo) / 2)
        if data[mid] < val:
            lo = mid + 1
        elif data[mid] > val:
            hi = mid - 1
        else:
            best_ind = mid
            break
        # check if data[mid] is closer to val than data[best_ind]
        if abs(data[mid] - val) < abs(data[best_ind] - val):
            best_ind = mid
    return best_ind


if __name__ == "__main__":
    data = [1544426700000.00, 1544426820000.00, 1544426880000.00, 1544430960000.00, 1544432220000.00, 1544438760000.00, 1544445600000.00, 1544481540000.00, 1544481720000.00, 1544485140000.00]
    val = 1544430930000.00
    print(binarySearch(data, val))