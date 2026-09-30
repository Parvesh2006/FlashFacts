
text = u'NASA\u2019s \u2026 \xb7 TNPSC-G4 \u2022'
bad_text = text.encode('utf-8').decode('windows-1252')
print('bad_text:', repr(bad_text))
fixed = bad_text.encode('windows-1252').decode('utf-8')
print('fixed:', repr(fixed))

