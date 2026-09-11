import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  fields: {
    complaint_source: '',
    customer_name: '',
    product_name: '',
    product_strength: '',
    batch_number: '',
    affected_quantity: '',
    manufacturing_date: '',
    expiry_date: '',
    originating_site_block: '',
    impacted_npm: '',
    defect_summary: '',
  },
  riskAssessment: null,
  capa: null,
  status: 'idle', // idle | loading | succeeded | failed  (network/AI call status)
  workflowStatus: 'Pending Triage', // Pending Triage | Under Review | Saved
  savedId: null,
}

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setStatus(state, action) {
      state.status = action.payload
    },
    setExtractedFields(state, action) {
      state.fields = { ...state.fields, ...action.payload }
    },
    setRiskAssessment(state, action) {
      state.riskAssessment = action.payload
    },
    setCapa(state, action) {
      state.capa = action.payload
    },
    setWorkflowStatus(state, action) {
      state.workflowStatus = action.payload
    },
    setSavedId(state, action) {
      state.savedId = action.payload
    },
    updateField(state, action) {
      const { name, value } = action.payload
      state.fields[name] = value
    },
    resetComplaint() {
      return initialState
    },
  },
})

export const {
  setStatus,
  setExtractedFields,
  setRiskAssessment,
  setCapa,
  setWorkflowStatus,
  setSavedId,
  updateField,
  resetComplaint,
} = complaintSlice.actions

export default complaintSlice.reducer
