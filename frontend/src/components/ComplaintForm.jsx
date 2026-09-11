import { useDispatch, useSelector } from 'react-redux'
import { updateField } from '../slices/complaintSlice.js'

const FIELD_LABELS = {
  complaint_source: 'Complaint Source',
  customer_name: 'Customer Name',
  product_name: 'Product Name',
  product_strength: 'Product Strength',
  batch_number: 'Batch / Lot Number',
  affected_quantity: 'Affected Quantity',
  manufacturing_date: 'Manufacturing Date',
  expiry_date: 'Expiry Date',
  originating_site_block: 'Originating Site Block',
  impacted_npm: 'Impacted Non-Product Materials (NPM)',
  defect_summary: 'Structured Defect Summary',
}

export default function ComplaintForm() {
  const dispatch = useDispatch()
  const fields = useSelector((state) => state.complaint.fields)

  const handleChange = (name) => (e) => {
    dispatch(updateField({ name, value: e.target.value }))
  }

  return (
    <div className="complaint-form">
      <h2>Log Customer Complaint</h2>
      <p className="subtitle">API &amp; FDF Quality Assurance Module</p>

      {Object.entries(FIELD_LABELS).map(([name, label]) =>
        name === 'defect_summary' ? (
          <div className="field" key={name}>
            <label>{label}</label>
            <textarea
              rows={4}
              value={fields[name]}
              onChange={handleChange(name)}
              placeholder="AI will synthesize the complaint into a formal QMS description..."
            />
          </div>
        ) : (
          <div className="field" key={name}>
            <label>{label}</label>
            <input
              type="text"
              value={fields[name]}
              onChange={handleChange(name)}
              placeholder="Awaiting AI extraction..."
            />
          </div>
        ),
      )}
    </div>
  )
}
