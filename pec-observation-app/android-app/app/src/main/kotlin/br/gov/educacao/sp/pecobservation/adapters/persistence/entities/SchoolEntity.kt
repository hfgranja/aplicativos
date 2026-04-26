package br.gov.educacao.sp.pecobservation.adapters.persistence.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import br.gov.educacao.sp.pecobservation.domain.entities.School
import java.time.Instant
import java.util.UUID

@Entity(tableName = "schools")
data class SchoolEntity(
    @PrimaryKey val id: String,
    val name: String,
    val inepCode: String,
    val address: String,
    val city: String,
    val createdAt: Long,
) {
    fun toDomain() = School(
        id        = UUID.fromString(id),
        name      = name,
        inepCode  = inepCode,
        address   = address,
        city      = city,
        createdAt = Instant.ofEpochMilli(createdAt),
    )

    companion object {
        fun from(s: School) = SchoolEntity(
            id        = s.id.toString(),
            name      = s.name,
            inepCode  = s.inepCode,
            address   = s.address,
            city      = s.city,
            createdAt = s.createdAt.toEpochMilli(),
        )
    }
}
