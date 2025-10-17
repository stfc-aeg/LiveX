import { checkNull } from '../../utils';

import React from "react";
import { TitleCard, WithEndpoint } from 'odin-react';
import ToggleSwitch from '../ToggleSwitch';
import DropdownSelector from '../DropdownSelector';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import FloatingLabel from 'react-bootstrap/FloatingLabel';
import { floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndpointSelect = WithEndpoint(Form.Select);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);

function DropdownTest(props){
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const dropdown_metadata = furnaceEndPoint.metadata.dropdown_test;

    return (
        <TitleCard
          title="test">
          <Row>
            <Col xs={6} sm={4}>
            <FloatingLabel
              label="test values:">
                <EndpointSelect
                  endpoint={furnaceEndPoint}
                  fullpath="dropdown_test"
                  variant='outline-secondary'
                  buttonText={furnaceEndPoint.data?.dropdown_test || "Unknown"}
                  style={floatingInputStyle}
                  disabled={connectedPuttingDisable}>
                    {(dropdown_metadata.allowed_values).map(
                        (selection, index) => (
                            <option value={selection} key={index}>{selection}</option>
                        )
                    )}
                </EndpointSelect>
            </FloatingLabel>
            </Col>
          </Row>
      </TitleCard>
    )
}

export default DropdownTest;