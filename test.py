from main import KeyFuck

kf = KeyFuck()
page1key = kf.create_page(kf.prime_memory_meter)
page2key = kf.create_page(kf.prime_memory_meter)

segment1key = kf.create_segment()
segment2key = kf.create_segment()

segment2 = kf.get_segment(segment2key)
segment2[0] = page1key
segment2[1] = page2key

segment1 = kf.get_segment(segment1key)
segment1[0] = segment2key

print(segment1.length(kf))
print(segment1.read(kf, 0))
