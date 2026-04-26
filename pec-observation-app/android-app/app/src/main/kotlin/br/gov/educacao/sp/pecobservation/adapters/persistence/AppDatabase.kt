package br.gov.educacao.sp.pecobservation.adapters.persistence

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Update
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.ObservationEntity
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.SchoolEntity
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.SyncCommandEntity
import br.gov.educacao.sp.pecobservation.adapters.persistence.entities.TeacherEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ObservationDao {
    @Query("SELECT * FROM observations ORDER BY createdAt DESC")
    fun observeAll(): Flow<List<ObservationEntity>>

    @Query("SELECT * FROM observations WHERE id = :id LIMIT 1")
    suspend fun findById(id: String): ObservationEntity?

    @Query("SELECT * FROM observations WHERE statusRaw = :status")
    suspend fun findByStatus(status: String): List<ObservationEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: ObservationEntity)

    @Query("DELETE FROM observations WHERE id = :id")
    suspend fun delete(id: String)
}

@Dao
interface SchoolDao {
    @Query("SELECT * FROM schools ORDER BY name ASC")
    fun observeAll(): Flow<List<SchoolEntity>>

    @Query("SELECT * FROM schools WHERE id = :id LIMIT 1")
    suspend fun findById(id: String): SchoolEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: SchoolEntity)
}

@Dao
interface TeacherDao {
    @Query("SELECT * FROM teachers WHERE schoolId = :schoolId ORDER BY fullName ASC")
    fun observeBySchool(schoolId: String): Flow<List<TeacherEntity>>

    @Query("SELECT * FROM teachers WHERE id = :id LIMIT 1")
    suspend fun findById(id: String): TeacherEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: TeacherEntity)
}

@Dao
interface SyncCommandDao {
    @Query("SELECT * FROM sync_commands WHERE statusRaw = 'PENDING' ORDER BY createdAt ASC")
    suspend fun findPending(): List<SyncCommandEntity>

    @Query("SELECT COUNT(*) FROM sync_commands WHERE statusRaw = 'PENDING'")
    suspend fun countPending(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: SyncCommandEntity)

    @Query("UPDATE sync_commands SET statusRaw = :status WHERE commandId = :id")
    suspend fun updateStatus(id: String, status: String)

    @Query("UPDATE sync_commands SET statusRaw = 'FAILED', retryCount = retryCount + 1, failureReason = :reason WHERE commandId = :id")
    suspend fun markFailed(id: String, reason: String)
}

@Database(
    entities = [
        ObservationEntity::class,
        SchoolEntity::class,
        TeacherEntity::class,
        SyncCommandEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun observationDao(): ObservationDao
    abstract fun schoolDao(): SchoolDao
    abstract fun teacherDao(): TeacherDao
    abstract fun syncCommandDao(): SyncCommandDao
}
