import r6

op = r6.Operator.get(r6.Operator.DefendOperatorType.SMOKE)
rnd = op.randomize()
print(rnd.weapons.primary.export())