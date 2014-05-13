import sys
import matplotlib.pyplot as plt

def paintbar(step = 20):
  d = []
  num = []
  maxdist = 0
  f = open("split_result", 'r')
  while 1:
    lines = f.readlines(1000)
    if not lines:
      break
    for line in lines:
      line = line.strip()
      words = line.split(':')
      if float(words[1]) > maxdist:
        maxdist = float(words[1])
  print "maxdist:%f" % (maxdist)
  maxidx = int(maxdist/step)
  for i in range(maxidx + 1): 
    d.append(i * step)
    num.append(0)

  f.seek(0, 0)
  while 1:
    lines = f.readlines(1000)
    if not lines:
      break
    for line in lines:
      line = line.strip()
      words = line.split(':')
      dist = float(words[1])
      for idx in range(maxidx):
        if dist >= idx * step and dist < idx * step + step:
          num[idx] = num[idx] + 1
          break
  print d, num

  plt.xlabel("length of section")
  plt.ylabel("frequency")
  plt.bar(left = d, height = num, width = step)
  plt.grid(True)
  plt.show()
  f.close()

if __name__ == "__main__":
  if len(sys.argv)!=2:
    print 'useby "paint.py step"'
    exit(1)
  else:
    step = sys.argv[1]
    print step
  paintbar(int(step))