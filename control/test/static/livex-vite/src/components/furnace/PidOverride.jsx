import React from 'react';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint } from 'odin-react';
import ToggleSwitch from '../ToggleSwitch';
import { checkNull  } from '../../utils';

import { floatingInputStyle, floatingLabelStyle } from '../../utils';
import { FloatingLabel } from 'react-bootstrap';


const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function PidOverride(props) {
    const {furnaceEndPoint} = props;
    const {connectedDisable} = props;
    const {title} = props;
    const {pid} = props;

    const labelWidth="100px";

    return (
      <TitleCard
        title={
          <Row>
            <Col xs={6} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>{title}</Col>
            <Col xs={3}>
              <EndPointButton
                endpoint={furnaceEndPoint}
                fullpath={pid+"/override/enable"}
                variant={furnaceEndPoint.data[pid]?.override?.enable ? 'danger' : 'primary'}
                value={furnaceEndPoint.data[pid]?.override?.enable ? false : true}
                >
                  {furnaceEndPoint.data[pid]?.override?.enable ? "Disable" : "Enable"}
              </EndPointButton>
            </Col>
          </Row>
        }>
        <Col>
          <FloatingLabel
              label="Output %">
              <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  fullpath={pid+"/override/percent_out"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
              />
          </FloatingLabel>
        </Col>
      </TitleCard>
    )
}

export default PidOverride;