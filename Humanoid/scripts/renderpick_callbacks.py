# The function below is called when any passed values have changed.
# Be sure to turn on the related parameter in the DAT to retrieve these values.
#
# me - this DAT
# renderPickDat - the connected Render Pick DAT
#
# events - a list of named tuples with the fields listed below.
# eventsPrev - a list of events holding the eventsPrev values.
#
#	u				- The selection u coordinate.			(float)
#	v				- The selection v coordinate.			(float)
#	select			- True when a selection is ongoing.		(bool)
#	selectStart		- True at the start of a selection.		(bool)
#	selectEnd		- True at the end of a selection.		(bool)
#	selectedOp		- First picked operator.				(OP)
#	selectedTexture	- Texture coordinate of selectedOp.		(Position)
#	pickOp			- Currently picked operator.			(OP)
#	pos				- 3D position of picked point.			(Position)
#	texture			- Texture coordinate of picked point.	(Position)
#	color			- Color of picked point.				(4-tuple)
#	normal			- Geometry normal of picked point.		(Vector)
#	depth			- Post projection space depth.			(float)
#	instanceId		- Instance ID of the object.			(int)
#	row				- The row associated with this event	(float)
#	inValues		- Dictionary of input DAT strings for the given row, where keys are column headers. (dict)
#	custom	 		- Dictionary of selected custom attributes

def onEvents(renderPickDat, events, eventsPrev):
	for event, eventPrev in zip(events, eventsPrev):
		if event.pickOp:
			if event.select:
				spawnRotationGuide(event.pickOp)
		else:
			spawnRotationGuide(None, False)
		pass

	return

def getObjectPos(selectedOp):
	return (
		selectedOp.center[0],
		selectedOp.center[1],
		selectedOp.center[2]
	)

def spawnRotationGuide(selectedOp=None, renderOn=True):
	rgOp = op('/user_interface/dev_UI/VisualPanel/Past/scenes/rot_guide')

	if selectedOp != None:
		rgInputPosOp = rgOp.op('input_position')

		x, y, z = getObjectPos(selectedOp)
		rgInputPosOp.par.value0 = x
		rgInputPosOp.par.value1 = y
		rgInputPosOp.par.value2 = z

	rgOp.render = renderOn

def toggleRotationRender(op, renderOn):
	xRotOp = op.op('x_rot')
	yRotOp = op.op('y_rot')
	zRotOp = op.op('z_rot')

	xRotOp.render = renderOn
	yRotOp.render = renderOn
	zRotOp.render = renderOn
