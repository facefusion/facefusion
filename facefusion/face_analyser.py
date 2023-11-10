from typing import Any, Optional, List
import threading
import insightface
import numpy

import facefusion.globals
from facefusion.face_cache import get_faces_cache, set_faces_cache
from facefusion.typing import Frame, Face, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender

class FaceAnalyser:
    def __init__(self):
        self.face_analyser = None
        self.thread_lock = threading.Lock()

    def get_face_analyser(self) -> Any:
        with self.thread_lock:
            if self.face_analyser is None:
                self.face_analyser = insightface.app.FaceAnalysis(name='buffalo_l', providers=facefusion.globals.execution_providers)
                self.face_analyser.prepare(ctx_id=0)
        return self.face_analyser

    def clear_face_analyser(self) -> None:
        with self.thread_lock:
            self.face_analyser = None

    def get_one_face(self, frame: Frame, position: int = 0) -> Optional[Face]:
        many_faces = self.get_many_faces(frame)
        if many_faces:
            try:
                return many_faces[position]
            except IndexError:
                return many_faces[-1]
        return None

    def get_many_faces(self, frame: Frame) -> List[Face]:
        try:
            faces_cache = get_faces_cache(frame)
            if faces_cache:
                faces = faces_cache
            else:
                faces = self.get_face_analyser().get(frame)
                set_faces_cache(frame, faces)
            if facefusion.globals.face_analyser_direction:
                faces = self.sort_by_direction(faces, facefusion.globals.face_analyser_direction)
            if facefusion.globals.face_analyser_age:
                faces = self.filter_by_age(faces, facefusion.globals.face_analyser_age)
            if facefusion.globals.face_analyser_gender:
                faces = self.filter_by_gender(faces, facefusion.globals.face_analyser_gender)
            return faces
        except (AttributeError, ValueError):
            return []

    @staticmethod
    def find_similar_faces(frame: Frame, reference_face: Face, face_distance: float) -> List[Face]:
        many_faces = get_many_faces(frame)
        similar_faces = []
        if many_faces:
            for face in many_faces:
                if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
                    current_face_distance = numpy.sum(numpy.square(face.normed_embedding - reference_face.normed_embedding))
                    if current_face_distance < face_distance:
                        similar_faces.append(face)
        return similar_faces

    @staticmethod
    def sort_by_direction(faces: List[Face], direction: FaceAnalyserDirection) -> List[Face]:
        if direction == FaceAnalyserDirection.LEFT_RIGHT:
            return sorted(faces, key=lambda face: face['bbox'][0])
        if direction == FaceAnalyserDirection.RIGHT_LEFT:
            return sorted(faces, key=lambda face: face['bbox'][0], reverse=True)
        if direction == FaceAnalyserDirection.TOP_BOTTOM:
            return sorted(faces, key=lambda face: face['bbox'][1])
        if direction == FaceAnalyserDirection.BOTTOM_TOP:
            return sorted(faces, key=lambda face: face['bbox'][1], reverse=True)
        if direction == FaceAnalyserDirection.SMALL_LARGE:
            return sorted(faces, key=lambda face: (face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1]))
        if direction == FaceAnalyserDirection.LARGE_SMALL:
            return sorted(faces, key=lambda face: (face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1]), reverse=True)
        return faces

    @staticmethod
    def filter_by_age(faces: List[Face], age: FaceAnalyserAge) -> List[Face]:
        filter_faces = []
        for face in faces:
            if face['age'] < 13 and age == FaceAnalyserAge.CHILD:
                filter_faces.append(face)
            elif face['age'] < 19 and age == FaceAnalyserAge.TEEN:
                filter_faces.append(face)
            elif face['age'] < 60 and age == FaceAnalyserAge.ADULT:
                filter_faces.append(face)
            elif face['age'] > 59 and age == FaceAnalyserAge.SENIOR:
                filter_faces.append(face)
        return filter_faces

    @staticmethod
    def filter_by_gender(faces: List[Face], gender: FaceAnalyserGender) -> List[Face]:
        filter_faces = []
        for face in faces:
            if face['gender'] == 1 and gender == FaceAnalyserGender.MALE:
                filter_faces.append(face)
            if face['gender'] == 0 and gender == FaceAnalyserGender.FEMALE:
                filter_faces.append(face)
        return filter_faces
