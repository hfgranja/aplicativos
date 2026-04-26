package br.gov.educacao.sp.pecobservation.di

import android.content.Context
import androidx.room.Room
import androidx.work.Configuration
import androidx.work.WorkManager
import br.gov.educacao.sp.pecobservation.adapters.persistence.AppDatabase
import br.gov.educacao.sp.pecobservation.adapters.persistence.ObservationDao
import br.gov.educacao.sp.pecobservation.adapters.persistence.RoomObservationRepository
import br.gov.educacao.sp.pecobservation.adapters.persistence.RoomSchoolRepository
import br.gov.educacao.sp.pecobservation.adapters.persistence.RoomSyncQueue
import br.gov.educacao.sp.pecobservation.adapters.persistence.RoomTeacherRepository
import br.gov.educacao.sp.pecobservation.adapters.persistence.SchoolDao
import br.gov.educacao.sp.pecobservation.adapters.persistence.SyncCommandDao
import br.gov.educacao.sp.pecobservation.adapters.persistence.TeacherDao
import br.gov.educacao.sp.pecobservation.adapters.recording.MediaRecorderAdapter
import br.gov.educacao.sp.pecobservation.adapters.network.RetrofitNetworkClient
import br.gov.educacao.sp.pecobservation.ports.AudioRecordingPort
import br.gov.educacao.sp.pecobservation.ports.NetworkClientPort
import br.gov.educacao.sp.pecobservation.ports.ObservationRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SchoolRepositoryPort
import br.gov.educacao.sp.pecobservation.ports.SyncQueuePort
import br.gov.educacao.sp.pecobservation.ports.TeacherRepositoryPort
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides @Singleton
    fun provideDatabase(@ApplicationContext ctx: Context): AppDatabase =
        Room.databaseBuilder(ctx, AppDatabase::class.java, "pec_observation.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides fun observationDao(db: AppDatabase): ObservationDao = db.observationDao()
    @Provides fun schoolDao(db: AppDatabase): SchoolDao = db.schoolDao()
    @Provides fun teacherDao(db: AppDatabase): TeacherDao = db.teacherDao()
    @Provides fun syncCommandDao(db: AppDatabase): SyncCommandDao = db.syncCommandDao()
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds @Singleton abstract fun observationRepo(impl: RoomObservationRepository): ObservationRepositoryPort
    @Binds @Singleton abstract fun schoolRepo(impl: RoomSchoolRepository): SchoolRepositoryPort
    @Binds @Singleton abstract fun teacherRepo(impl: RoomTeacherRepository): TeacherRepositoryPort
    @Binds @Singleton abstract fun syncQueue(impl: RoomSyncQueue): SyncQueuePort
    @Binds @Singleton abstract fun recorder(impl: MediaRecorderAdapter): AudioRecordingPort
    @Binds @Singleton abstract fun networkClient(impl: RetrofitNetworkClient): NetworkClientPort
}

@Module
@InstallIn(SingletonComponent::class)
object WorkManagerModule {
    @Provides @Singleton
    fun workManagerConfig(
        workerFactory: androidx.hilt.work.HiltWorkerFactory,
    ): Configuration = Configuration.Builder()
        .setWorkerFactory(workerFactory)
        .build()
}
