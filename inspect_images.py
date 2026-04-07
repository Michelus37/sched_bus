from PIL import Image
import numpy as np
from pathlib import Path

for p in sorted(Path('screens').glob('*.jpg')):
    img = Image.open(p)
    arr = np.array(img)
    gray = arr.mean(axis=2)
    print(p.name, img.size, f'avg={gray.mean():.2f}', f'min={gray.min():.2f}', f'max={gray.max():.2f}')
    row_sum = (gray < 240).sum(axis=1)
    col_sum = (gray < 240).sum(axis=0)
    rows = np.where(row_sum > 0)[0]
    cols = np.where(col_sum > 0)[0]
    print('rows', rows[:3].tolist(), rows[-3:].tolist(), 'cols', cols[:3].tolist(), cols[-3:].tolist())
    print('---')
