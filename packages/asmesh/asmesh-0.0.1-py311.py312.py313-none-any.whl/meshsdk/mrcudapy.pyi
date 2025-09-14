from __future__ import annotations
import meshsdk.mrmeshpy
from meshsdk.mrmeshpy import func_bool_from_float
from meshsdk.mrmeshpy import func_tl_expected_void_std_string_from_std_vector_float_Vector3_int_int
from meshsdk.mrmeshpy import int_output
from meshsdk.mrmeshpy import std_vector_MeshIntersectionResult
from meshsdk.mrmeshpy import std_vector_MeshProjectionResult
from meshsdk.mrmeshpy import std_vector_MeshTriPoint
from meshsdk.mrmeshpy import std_vector_PointsProjectionResult
from meshsdk.mrmeshpy import std_vector_SkyPatch
from meshsdk.mrmeshpy import std_vector_Vector3_float as std_vector_Vector3f
from meshsdk.mrmeshpy import std_vector_Vector3_float
from meshsdk.mrmeshpy import std_vector_float
import typing
__all__: list[str] = ['FastWindingNumber', 'PointsProjector', 'PointsToMeshProjector', 'computeDistanceMap', 'computeDistanceMapHeapBytes', 'computeSkyViewFactor', 'distanceMapFromContours', 'distanceMapFromContoursHeapBytes', 'findProjectionOnPoints', 'findProjectionOnPointsHeapBytes', 'findSkyRays', 'func_bool_from_float', 'func_tl_expected_void_std_string_from_VoxelsVolumeMinMax_Vector_float_Id_VoxelTag_int', 'func_tl_expected_void_std_string_from_std_vector_float_Vector3_int_int', 'getCudaAvailableMemory', 'getCudaSafeMemoryLimit', 'int_output', 'isCudaAvailable', 'loadMRCudaDll', 'maxBufferSize', 'maxBufferSizeAlignedByBlock', 'negatePicture', 'pointsToDistanceVolume', 'pointsToDistanceVolumeByParts', 'std_vector_MeshIntersectionResult', 'std_vector_MeshProjectionResult', 'std_vector_MeshTriPoint', 'std_vector_PointsProjectionResult', 'std_vector_SkyPatch', 'std_vector_Vector3_float', 'std_vector_Vector3f', 'std_vector_float']
class FastWindingNumber(meshsdk.mrmeshpy.IFastWindingNumber, meshsdk.mrmeshpy.IFastWindingNumberByParts):
    """
    Generated from:  MR::Cuda::FastWindingNumber
    
    the class for fast approximate computation of winding number for a mesh (using its AABB tree)
    """
    @staticmethod
    @typing.overload
    def __init__(*args, **kwargs) -> None:
        ...
    @typing.overload
    def __init__(self, mesh: meshsdk.mrmeshpy.Mesh) -> None:
        """
        constructs this from AABB tree of given mesh;
        """
    @typing.overload
    def __init__(self, arg0: FastWindingNumber) -> None:
        """
        Implicit copy constructor.
        """
    def calcFromGrid(self, res: meshsdk.mrmeshpy.std_vector_float, dims: meshsdk.mrmeshpy.Vector3i, gridToMeshXf: meshsdk.mrmeshpy.AffineXf3f, beta: float, cb: meshsdk.mrmeshpy.func_bool_from_float) -> None:
        ...
    def calcFromGridByParts(self, resFunc: meshsdk.mrmeshpy.func_tl_expected_void_std_string_from_std_vector_float_Vector3_int_int, dims: meshsdk.mrmeshpy.Vector3i, gridToMeshXf: meshsdk.mrmeshpy.AffineXf3f, beta: float, layerOverlap: int, cb: meshsdk.mrmeshpy.func_bool_from_float) -> None:
        """
        see methods' descriptions in IFastWindingNumberByParts
        """
    def calcFromGridWithDistances(self, res: meshsdk.mrmeshpy.std_vector_float, dims: meshsdk.mrmeshpy.Vector3i, gridToMeshXf: meshsdk.mrmeshpy.AffineXf3f, options: meshsdk.mrmeshpy.DistanceToMeshOptions, cb: meshsdk.mrmeshpy.func_bool_from_float) -> None:
        ...
    def calcFromGridWithDistancesByParts(self, resFunc: meshsdk.mrmeshpy.func_tl_expected_void_std_string_from_std_vector_float_Vector3_int_int, dims: meshsdk.mrmeshpy.Vector3i, gridToMeshXf: meshsdk.mrmeshpy.AffineXf3f, options: meshsdk.mrmeshpy.DistanceToMeshOptions, layerOverlap: int, cb: meshsdk.mrmeshpy.func_bool_from_float) -> None:
        ...
    def calcFromVector(self, res: meshsdk.mrmeshpy.std_vector_float, points: meshsdk.mrmeshpy.std_vector_Vector3_float, beta: float, skipFace: meshsdk.mrmeshpy.FaceId, cb: meshsdk.mrmeshpy.func_bool_from_float) -> None:
        """
        see methods' descriptions in IFastWindingNumber
        """
    def calcSelfIntersections(self, res: meshsdk.mrmeshpy.FaceBitSet, beta: float, cb: meshsdk.mrmeshpy.func_bool_from_float) -> None:
        ...
class PointsProjector(meshsdk.mrmeshpy.IPointsProjector):
    """
    Generated from:  MR::Cuda::PointsProjector
    
    CUDA-backed implementation of IPointsProjector
    """
    @staticmethod
    @typing.overload
    def __init__(*args, **kwargs) -> None:
        ...
    @staticmethod
    @typing.overload
    def operator(*args, **kwargs) -> PointsProjector:
        ...
    @staticmethod
    @typing.overload
    def operator(*args, **kwargs) -> PointsProjector:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: PointsProjector) -> None:
        """
        Implicit copy constructor.
        """
    def findProjections(self, results: meshsdk.mrmeshpy.std_vector_PointsProjectionResult, points: meshsdk.mrmeshpy.std_vector_Vector3_float, settings: meshsdk.mrmeshpy.FindProjectionOnPointsSettings) -> None:
        """
        computes the closest points on point cloud to given points
        """
    def projectionsHeapBytes(self, numProjections: int) -> int:
        """
        Returns amount of additional memory needed to compute projections
        """
    def setPointCloud(self, pointCloud: meshsdk.mrmeshpy.PointCloud) -> None:
        """
        sets the reference point cloud
        """
class PointsToMeshProjector(meshsdk.mrmeshpy.IPointsToMeshProjector):
    """
    Generated from:  MR::Cuda::PointsToMeshProjector
    
    Computes the closest point on mesh to each of given points on GPU. It caches data that necessary for computing
    """
    @staticmethod
    @typing.overload
    def __init__(*args, **kwargs) -> None:
        ...
    @staticmethod
    @typing.overload
    def operator(*args, **kwargs) -> PointsToMeshProjector:
        ...
    @staticmethod
    @typing.overload
    def operator(*args, **kwargs) -> PointsToMeshProjector:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: PointsToMeshProjector) -> None:
        """
        Implicit copy constructor.
        """
    def findProjections(self, res: meshsdk.mrmeshpy.std_vector_MeshProjectionResult, points: meshsdk.mrmeshpy.std_vector_Vector3_float, objXf: meshsdk.mrmeshpy.AffineXf3f, refObjXf: meshsdk.mrmeshpy.AffineXf3f, upDistLimitSq: float, loDistLimitSq: float) -> None:
        """
        <summary>
        Computes the closest point on mesh to each of given points
        </summary>
        <param name="res">vector pf projections</param>
        <param name="points">vector of points to project</param>
        <param name="objXf">transform applied to points</param>
        <param name="refObjXf">transform applied to referencing mesh</param>
        <param name="upDistLimitSq">maximal squared distance from point to mesh</param>
        <param name="loDistLimitSq">minimal squared distance from point to mesh</param>
        """
    def projectionsHeapBytes(self, numProjections: int) -> int:
        """
        Returns amount of additional memory needed to compute projections
        """
    def updateMeshData(self, mesh: meshsdk.mrmeshpy.Mesh) -> None:
        """
        update all data related to the referencing mesh
        """
class func_tl_expected_void_std_string_from_VoxelsVolumeMinMax_Vector_float_Id_VoxelTag_int:
    def __bool__(self) -> bool:
        ...
    def __call__(self, arg0: meshsdk.mrmeshpy.SimpleVolumeMinMax, arg1: int) -> None:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: None) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: func_tl_expected_void_std_string_from_VoxelsVolumeMinMax_Vector_float_Id_VoxelTag_int) -> None:
        ...
    def can_be_created_from_python(self) -> bool:
        """
        If false, this function type can't hold a Python function, and can only be created from C++.
        """
    def holds_cpp_function(self) -> bool:
        """
        Does this object currentlyhold a C++ function? As opposed to a Python one.
        """
def computeDistanceMap(mesh: meshsdk.mrmeshpy.Mesh, params: meshsdk.mrmeshpy.MeshToDistanceMapParams, cb: meshsdk.mrmeshpy.func_bool_from_float = '{}', outSamples: meshsdk.mrmeshpy.std_vector_MeshTriPoint = None) -> meshsdk.mrmeshpy.DistanceMap:
    """
    computes distance (height) map for given projection parameters
    using float-precision for finding ray-mesh intersections, which is faster but less reliable
    """
def computeDistanceMapHeapBytes(mesh: meshsdk.mrmeshpy.Mesh, params: meshsdk.mrmeshpy.MeshToDistanceMapParams, needOutSamples: bool = False) -> int:
    """
    Computes memory consumption of computeDistanceMap function
    """
def computeSkyViewFactor(terrain: meshsdk.mrmeshpy.Mesh, samples: meshsdk.mrmeshpy.VertCoords, validSamples: meshsdk.mrmeshpy.VertBitSet, skyPatches: meshsdk.mrmeshpy.std_vector_SkyPatch, outSkyRays: meshsdk.mrmeshpy.BitSet = None, outIntersections: meshsdk.mrmeshpy.std_vector_MeshIntersectionResult = None) -> meshsdk.mrmeshpy.VertScalars:
    """
    computes relative radiation in each valid sample point by emitting rays from that point in the sky:
    the radiation is 1.0f if all rays reach the sky not hitting the terrain;
    the radiation is 0.0f if all rays do not reach the sky because they are intercepted by the terrain;
    \\param outSkyRays - optional output bitset where for every valid sample #i its rays are stored at indices [i*numPatches; (i+1)*numPatches),
                        0s for occluded rays (hitting the terrain) and 1s for the ones which don't hit anything and reach the sky
    \\param outIntersections - optional output vector of MeshIntersectionResult for every valid sample point
    """
def distanceMapFromContours(polyline: meshsdk.mrmeshpy.Polyline2, params: meshsdk.mrmeshpy.ContourToDistanceMapParams) -> meshsdk.mrmeshpy.DistanceMap:
    """
    Computes distance of 2d contours according to ContourToDistanceMapParams (works correctly only when withSign==false)
    """
def distanceMapFromContoursHeapBytes(polyline: meshsdk.mrmeshpy.Polyline2, params: meshsdk.mrmeshpy.ContourToDistanceMapParams) -> int:
    """
    Computes memory consumption of distanceMapFromContours function
    """
def findProjectionOnPoints(pointCloud: meshsdk.mrmeshpy.PointCloud, points: meshsdk.mrmeshpy.std_vector_Vector3_float, settings: meshsdk.mrmeshpy.FindProjectionOnPointsSettings = '{}') -> meshsdk.mrmeshpy.std_vector_PointsProjectionResult:
    """
    computes the closest points on point cloud to given points
    """
def findProjectionOnPointsHeapBytes(pointCloud: meshsdk.mrmeshpy.PointCloud, pointsCount: int) -> int:
    """
    returns the minimal amount of free GPU memory required for \\ref MR::Cuda::findProjectionOnPoints
    """
def findSkyRays(terrain: meshsdk.mrmeshpy.Mesh, samples: meshsdk.mrmeshpy.VertCoords, validSamples: meshsdk.mrmeshpy.VertBitSet, skyPatches: meshsdk.mrmeshpy.std_vector_SkyPatch, outIntersections: meshsdk.mrmeshpy.std_vector_MeshIntersectionResult = None) -> meshsdk.mrmeshpy.BitSet:
    """
    In each valid sample point tests the rays from that point in the sky;
    \\return bitset where for every valid sample #i its rays are stored at indices [i*numPatches; (i+1)*numPatches),
            0s for occluded rays (hitting the terrain) and 1s for the ones which don't hit anything and reach the sky
    \\param outIntersections - optional output vector of MeshIntersectionResult for every valid sample point
    """
def getCudaAvailableMemory() -> int:
    """
    Returns available GPU memory in bytes
    """
def getCudaSafeMemoryLimit() -> int:
    """
    Returns maximum safe amount of free GPU memory that will be used for dynamic-sized buffers
    """
def isCudaAvailable(driverVersion: meshsdk.mrmeshpy.int_output = None, runtimeVersion: meshsdk.mrmeshpy.int_output = None, computeMajor: meshsdk.mrmeshpy.int_output = None, computeMinor: meshsdk.mrmeshpy.int_output = None) -> bool:
    """
    Returns true if Cuda is present on this GPU
    optional out maximum driver supported version
    optional out current runtime version
    optional out compute capability major version
    optional out compute capability minor version
    """
def loadMRCudaDll() -> None:
    """
    call this function to load MRCuda shared library
    """
def maxBufferSize(availableBytes: int, elementCount: int, elementBytes: int) -> int:
    """
    Returns maximum buffer size in elements that can be allocated with given memory limit
    """
@typing.overload
def maxBufferSizeAlignedByBlock(availableBytes: int, blockDims: meshsdk.mrmeshpy.Vector2i, elementBytes: int) -> int:
    """
    Returns maximum buffer size in elements that can be allocated with given memory limit
    The size is aligned to the block dimensions
    """
@typing.overload
def maxBufferSizeAlignedByBlock(availableBytes: int, blockDims: meshsdk.mrmeshpy.Vector3i, elementBytes: int) -> int:
    ...
def negatePicture(image: meshsdk.mrmeshpy.Image) -> None:
    """
    This function inverts Color value (255 - value in each channel except alpha) 
    """
def pointsToDistanceVolume(cloud: meshsdk.mrmeshpy.PointCloud, params: meshsdk.mrmeshpy.PointsToDistanceVolumeParams) -> meshsdk.mrmeshpy.SimpleVolumeMinMax:
    """
    makes SimpleVolume filled with signed distances to points with normals
    """
def pointsToDistanceVolumeByParts(cloud: meshsdk.mrmeshpy.PointCloud, params: meshsdk.mrmeshpy.PointsToDistanceVolumeParams, addPart: func_tl_expected_void_std_string_from_VoxelsVolumeMinMax_Vector_float_Id_VoxelTag_int, layerOverlap: int) -> None:
    """
    makes SimpleVolume filled with signed distances to points with normals
    populate the volume by parts to the given callback
    """
