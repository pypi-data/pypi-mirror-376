from compas.geometry import Box
from compas.geometry import Cylinder
from compas.geometry import Sphere
from compas_model.elements import Element
from compas_pb.conversions import box_from_pb
from compas_pb.conversions import box_to_pb
from compas_pb.conversions import cylinder_from_pb
from compas_pb.conversions import cylinder_to_pb
from compas_pb.conversions import frame_from_pb
from compas_pb.conversions import frame_to_pb
from compas_pb.conversions import mesh_from_pb
from compas_pb.conversions import mesh_to_pb
from compas_pb.conversions import sphere_from_pb
from compas_pb.conversions import sphere_to_pb
from compas_pb.core import any_from_pb
from compas_pb.core import any_to_pb
from compas_pb.registry import pb_deserializer
from compas_pb.registry import pb_serializer
from compas_timber.elements import Beam
from compas_timber.fabrication import BTLxProcessing
from compas_timber.planning import BuildingPlan
from compas_timber.planning import Step

from compas_timber_pb.generated import building_plan_pb2
from compas_timber_pb.generated import elements_pb2
from compas_timber_pb.generated import processing_pb2
from compas_timber_pb.planning import BuildingPlanModelContainer


@pb_serializer(BuildingPlanModelContainer)
def buildingplanmodelcontainer_to_pb(obj: BuildingPlanModelContainer) -> building_plan_pb2.BuildingPlanModelContainerData:
    proto_data = building_plan_pb2.BuildingPlanModelContainerData()
    proto_data.plan.CopyFrom(buildingplan_to_pb(obj.plan))

    for guid, element in obj.elements.items():
        proto_element = building_plan_pb2.Element()
        if isinstance(element, Beam):
            proto_element.beam.CopyFrom(beam_to_pb(element))
        elif isinstance(element, Element):
            proto_element.element.CopyFrom(element_to_pb(element))
        proto_data.elements[guid].CopyFrom(proto_element)

    for guid, geometry in obj.geometries.items():
        proto_geometry = building_plan_pb2.ElementGeometry()
        if isinstance(geometry, str):
            proto_geometry.firebaseFilename = geometry
        elif isinstance(geometry, Box):
            proto_geometry.box.CopyFrom(box_to_pb(geometry))
        elif isinstance(geometry, Cylinder):
            proto_geometry.cylinder.CopyFrom(cylinder_to_pb(geometry))
        elif isinstance(geometry, Sphere):
            proto_geometry.sphere.CopyFrom(sphere_to_pb(geometry))
        elif hasattr(geometry, "to_mesh"):
            proto_geometry.mesh.CopyFrom(mesh_to_pb(geometry.to_mesh()))
        proto_data.geometries[guid].CopyFrom(proto_geometry)

    return proto_data


@pb_deserializer(building_plan_pb2.BuildingPlanModelContainerData)
def buildingplanmodelcontainer_from_pb(proto_data: building_plan_pb2.BuildingPlanModelContainerData) -> BuildingPlanModelContainer:
    plan = buildingplan_from_pb(proto_data.plan)
    elements = {}

    for guid, proto_element in proto_data.elements.items():
        if proto_element.HasField("beam"):
            elements[guid] = beam_from_pb(proto_element.beam)
        elif proto_element.HasField("element"):
            elements[guid] = element_from_pb(proto_element.element)

    geometries = {}
    for guid, proto_geometry in proto_data.geometries.items():
        if proto_geometry.HasField("firebaseFilename"):
            geometries[guid] = proto_geometry.firebaseFilename
        elif proto_geometry.HasField("box"):
            geometries[guid] = box_from_pb(proto_geometry.box)
        elif proto_geometry.HasField("cylinder"):
            geometries[guid] = cylinder_from_pb(proto_geometry.cylinder)
        elif proto_geometry.HasField("sphere"):
            geometries[guid] = sphere_from_pb(proto_geometry.sphere)
        elif proto_geometry.HasField("mesh"):
            geometries[guid] = mesh_from_pb(proto_geometry.mesh)

    return BuildingPlanModelContainer(plan, elements, geometries)


@pb_serializer(Beam)
def beam_to_pb(obj: Beam) -> elements_pb2.BeamData:
    """Convert a Beam object to a protobuf message.

    Parameters
    ----------
    obj : Beam
        The Beam object to convert.

    Returns
    -------
    elements_pb2.BeamData
        The protobuf message representation of the Beam.
    """
    proto_data = elements_pb2.BeamData()
    proto_data.guid = str(obj.guid)
    proto_data.name = obj.name
    proto_data.length = obj.length
    proto_data.width = obj.width
    proto_data.height = obj.height
    frame = frame_to_pb(obj.frame)

    proto_data.frame.CopyFrom(frame)
    return proto_data


@pb_deserializer(elements_pb2.BeamData)
def beam_from_pb(proto_data: elements_pb2.BeamData) -> Beam:
    """Convert a protobuf message to a Beam object.

    Parameters
    ----------
    proto_data : elements_pb2.BeamData
        The protobuf message to convert.

    Returns
    -------
    Beam
        The reconstructed Beam object.
    """
    frame = frame_from_pb(proto_data.frame)
    beam = Beam(
        frame=frame,
        length=proto_data.length,
        width=proto_data.width,
        height=proto_data.height,
        name=proto_data.name,
    )
    beam._guid = proto_data.guid
    return beam


@pb_serializer(Element)
def element_to_pb(obj: Element) -> elements_pb2.ElementData:
    """Convert an Element object to a protobuf message.

    Parameters
    ----------
    obj : Element
        The Element object to convert.

    Returns
    -------
    elements_pb2.ElementData
        The protobuf message representation of the Element.
    """
    proto_data = elements_pb2.ElementData()
    proto_data.guid = str(obj.guid)
    proto_data.name = obj.name

    frame = frame_to_pb(obj.frame)
    proto_data.frame.CopyFrom(frame)

    mesh = mesh_to_pb(obj.geometry)
    proto_data.geometry.CopyFrom(mesh)

    return proto_data


@pb_deserializer(elements_pb2.ElementData)
def element_from_pb(proto_data: elements_pb2.ElementData) -> Element:
    """Convert a protobuf message to an Element object.

    Parameters
    ----------
    proto_data : elements_pb2.ElementData
        The protobuf message to convert.

    Returns
    -------
    Element
        The reconstructed Element object.
    """
    frame = frame_from_pb(proto_data.frame)
    mesh = mesh_from_pb(proto_data.geometry)
    element = Element(frame=frame, name=proto_data.name, geometry=mesh)
    element._guid = proto_data.guid
    return element


@pb_serializer(BTLxProcessing)
def processing_to_pb(obj: BTLxProcessing) -> processing_pb2.BTLxProcessingData:
    """Convert a BTLxProcessing object to a protobuf message.

    Parameters
    ----------
    obj : BTLxProcessing
        The BTLxProcessing object to convert.

    Returns
    -------
    processing_pb2.BTLxProcessingData
        The protobuf message representation of the BTLxProcessing object.
    """
    proto_data = processing_pb2.BTLxProcessingData()
    proto_data.name = obj.PROCESSING_NAME
    proto_data.guid = str(obj.guid)

    for key, value in obj.__data__.items():
        data = any_to_pb(value)
        proto_data.params[key].CopyFrom(data)

    return proto_data


def _fetch_processing_cls_by_name(name: str):
    """Fetch the processing class by name.

    Parameters
    ----------
    name : str
        The name of the processing class to fetch.

    Returns
    -------
    type
        The processing class with the specified name.

    Raises
    ------
    ValueError
        If no processing class with the specified name is found.
    """
    for cls in BTLxProcessing.__subclasses__():
        if cls.PROCESSING_NAME == name:
            return cls
    raise ValueError(f"Processing class with name '{name}' not found.")


@pb_deserializer(processing_pb2.BTLxProcessingData)
def processing_from_pb(proto_data: processing_pb2.BTLxProcessingData) -> BTLxProcessing:
    """Convert a protobuf message to a BTLxProcessing object.

    Parameters
    ----------
    proto_data : processing_pb2.BTLxProcessingData
        The protobuf message to convert.

    Returns
    -------
    BTLxProcessing
        The reconstructed BTLxProcessing object.
    """

    cls = _fetch_processing_cls_by_name(proto_data.name)
    data_dict = {}
    for key, value in proto_data.params.items():
        data = any_from_pb(value)
        data_dict[key] = data
    instance = cls.__from_data__(data_dict)
    instance._guid = proto_data.guid  # TODO: should be able to send this to __from_data__, or is it __from_json__?
    return instance


@pb_serializer(BuildingPlan)
def buildingplan_to_pb(obj: BuildingPlan) -> building_plan_pb2.BuildingPlanData:
    """Convert a BuildingPlan object to a protobuf message.

    Parameters
    ----------
    obj : BuildingPlan
        The BuildingPlan object to convert.

    Returns
    -------
    building_plan_pb2.BuildingPlanData
        The protobuf message representation of the BuildingPlan.
    """
    proto_data = building_plan_pb2.BuildingPlanData()
    proto_data.guid = str(obj.guid)
    proto_data.name = obj.name

    for step in obj.steps:
        proto_step = building_plan_pb2.StepData()
        proto_step.name = step.name
        proto_step.guid = str(step.guid)
        proto_step.elementGuids.extend(step.element_ids)
        proto_step.elementHeld.extend(step.elements_held)
        proto_step.isBuilt = step.is_built
        proto_step.isPlanned = step.is_planned
        proto_step.actor = step.actor
        proto_step.priority = step.priority
        proto_data.steps.append(proto_step)

    return proto_data


@pb_deserializer(building_plan_pb2.BuildingPlanData)
def buildingplan_from_pb(proto_data: building_plan_pb2.BuildingPlanData) -> BuildingPlan:
    """Convert a protobuf message to a BuildingPlan object.

    Parameters
    ----------
    proto_data : building_plan_pb2.BuildingPlanData
        The protobuf message to convert.

    Returns
    -------
    BuildingPlan
        The reconstructed BuildingPlan object.
    """
    plan = BuildingPlan()
    plan.name = proto_data.name
    plan._guid = proto_data.guid

    for step in proto_data.steps:
        step_obj = Step(
            element_ids=list(step.elementGuids), elements_held=list(step.elementHeld), is_built=step.isBuilt, is_planned=step.isPlanned, actor=step.actor, priority=step.priority
        )
        step_obj.name = step.name
        step_obj._guid = step.guid
        plan.add_step(step_obj)

    return plan
