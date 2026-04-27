export interface School {
  id: string
  inepCode: string
  name: string
  city: string
  state: string
  address?: string
  principalName?: string
  isActive: boolean
  createdAt: string
}

export interface Teacher {
  id: string
  schoolId: string
  name: string
  email: string
  subjectArea: string
  employeeId?: string
  isActive: boolean
  createdAt: string
}
