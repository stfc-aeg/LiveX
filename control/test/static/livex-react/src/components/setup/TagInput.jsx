import React from 'react';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { useState, useMemo } from 'react';
import { MultiSelect } from 'react-multi-select-component';
import { WithEndpoint } from 'odin-react';

const EndPointButton = WithEndpoint(Button);

function TagInput(props) {
    const {options} = props;
    const {metadataEndPoint} = props;
    const {field} = props;

    const selectOptions = options.map(value => ({
      label: value,
      value: value,
      disabled: false
    }));

    const [selected, setSelected] = useState([]);
    const [values, setValues] = useState([]);

    const handleOnChange = (selectedOptions) => {
      setSelected(selectedOptions);

      const selectedValues = selectedOptions.map(option => option.value);
      setValues(selectedValues);
    }

    return (
      <InputGroup>
        <InputGroup.Text>
          Experiment Tags
        </InputGroup.Text>
        <MultiSelect
          options={selectOptions}
          value={selected}
          onChange={handleOnChange}
          labelledBy="Select tags"
          hasSelectAll={false}
        />
        <EndPointButton
          endpoint={metadataEndPoint}
          value={values}
          fullpath={"fields/"+field+"/value"}
          event_type="click"
          variant="outline-primary"
        >Send values</EndPointButton>
      </InputGroup>
    )
}

export default TagInput

