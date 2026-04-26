package br.gov.educacao.sp.pecobservation.adapters.persistence.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import br.gov.educacao.sp.pecobservation.domain.entities.Teacher
import java.time.Instant
import java.util.UUID

@Entity(
    tableName = "teachers",
    foreignKeys = [ForeignKey(
        entity        = SchoolEntity::class,
        parentColumns = ["id"],
        childColumns  = ["schoolId"],
        onDelete      = ForeignKey.CASCADE,
    )],
    indices = [Index("schoolId")],
)
data class TeacherEntity(
    @PrimaryKey val id: String,
    val schoolId: String,
    val fullName: String,
    val subjectArea: String,
    val createdAt: Long,
) {
    fun toDomain() = Teacher(
        id          = UUID.fromString(id),
        schoolId    = UUID.fromString(schoolId),
        fullName    = fullName,
        subjectArea = subjectArea,
        createdAt   = Instant.ofEpochMilli(createdAt),
    )

    companion object {
        fun from(t: Teacher) = TeacherEntity(
            id          = t.id.toString(),
            schoolId    = t.schoolId.toString(),
            fullName    = t.fullName,
            subjectArea = t.subjectArea,
            createdAt   = t.createdAt.toEpochMilli(),
        )
    }
}
