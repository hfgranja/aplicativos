package br.gov.educacao.sp.pecobservation.ports

import br.gov.educacao.sp.pecobservation.domain.entities.School
import br.gov.educacao.sp.pecobservation.domain.entities.Teacher
import kotlinx.coroutines.flow.Flow
import java.util.UUID

interface SchoolRepositoryPort {
    fun observeAll(): Flow<List<School>>
    suspend fun save(school: School)
    suspend fun fetchById(id: UUID): School?
}

interface TeacherRepositoryPort {
    fun observeBySchool(schoolId: UUID): Flow<List<Teacher>>
    suspend fun save(teacher: Teacher)
    suspend fun fetchById(id: UUID): Teacher?
}
